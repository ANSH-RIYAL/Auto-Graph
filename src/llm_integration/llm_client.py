"""
Simple LLM client for OpenAI integration.
Handles API calls and response processing.
"""

import json
import hashlib
from typing import Dict, Any, Optional
from pathlib import Path
import openai
from ..config.settings import settings
from ..utils.logger import get_logger

logger = get_logger(__name__)


class LLMClient:
    """Simple LLM client for OpenAI API integration."""
    
    def __init__(self):
        self.client = None
        self.cache_dir = Path("cache/llm")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        if settings.validate_llm_config():
            try:
                # Initialize OpenAI client with proper configuration
                self.client = openai.OpenAI(
                    api_key=settings.OPENAI_API_KEY,
                    # Remove any problematic parameters that might cause issues
                )
                logger.info("LLM client initialized successfully")
            except Exception as e:
                logger.warning(f"LLM client initialization failed: {e}")
                self.client = None
        else:
            logger.warning("LLM client not initialized - missing configuration")
    
    def analyze_component(self, file_path: str, file_content: str, symbols: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a code component using LLM."""
        if not self.client:
            logger.warning("LLM client not available, using fallback analysis")
            return self._fallback_analysis(file_path, symbols)
        
        # Create cache key
        cache_key = self._generate_cache_key(file_path, file_content, symbols)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        # Check cache first
        if settings.LLM_CACHE_ENABLED and cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    cached_result = json.load(f)
                logger.debug(f"Using cached LLM analysis for {file_path}")
                return cached_result
            except Exception as e:
                logger.warning(f"Failed to load cached result: {e}")
        
        # Prepare prompt
        prompt = self._create_analysis_prompt(file_path, file_content, symbols)
        
        try:
            # Make API call
            response = self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=settings.LLM_MAX_TOKENS,
                temperature=settings.LLM_TEMPERATURE
            )
            
            # Parse response
            result = self._parse_llm_response(response.choices[0].message.content)
            
            # Cache result
            if settings.LLM_CACHE_ENABLED:
                try:
                    with open(cache_file, 'w') as f:
                        json.dump(result, f, indent=2)
                except Exception as e:
                    logger.warning(f"Failed to cache result: {e}")
            
            logger.debug(f"LLM analysis completed for {file_path}")
            return result
            
        except Exception as e:
            logger.error(f"LLM analysis failed for {file_path}: {e}")
            return self._fallback_analysis(file_path, symbols)
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for LLM analysis."""
        return """You are an expert software architect analyzing code components for a hierarchical graph representation.

Your task is to analyze code files and determine:
1. The component's purpose and responsibility
2. Whether it belongs to High-Level Design (HLD) or Low-Level Design (LLD)
3. The component type (Module, API, Service, Function, Class, etc.)
4. Complexity level (low, medium, high)
5. Key relationships and dependencies

Respond with a JSON object containing:
{
    "purpose": "Brief description of what this component does",
    "level": "HLD" or "LLD",
    "component_type": "Module|API|Service|Function|Class|Utility|Controller|Model",
    "complexity": "low|medium|high",
    "relationships": ["list", "of", "key", "dependencies"],
    "confidence": 0.0-1.0
}

Keep responses concise and focused on architectural understanding."""
    
    def _create_analysis_prompt(self, file_path: str, file_content: str, symbols: Dict[str, Any]) -> str:
        """Create a prompt for analyzing a code component."""
        file_name = Path(file_path).name
        
        # Get a preview of the file content (first 500 characters)
        content_preview = file_content[:500] + "..." if len(file_content) > 500 else file_content
        
        prompt = f"""Analyze this code component:

File: {file_path}
File Name: {file_name}

Functions: {symbols.get('functions', [])}
Classes: {symbols.get('classes', [])}
Imports: {symbols.get('imports', [])}

Content Preview:
{content_preview}

Provide a JSON analysis of this component's role in the system architecture."""
        
        return prompt
    
    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """Parse the LLM response into a structured format."""
        try:
            # Try to extract JSON from response
            if '{' in response and '}' in response:
                start = response.find('{')
                end = response.rfind('}') + 1
                json_str = response[start:end]
                result = json.loads(json_str)
            else:
                # Fallback parsing
                result = self._parse_text_response(response)
            
            # Validate and normalize result
            return self._normalize_result(result)
            
        except Exception as e:
            logger.warning(f"Failed to parse LLM response: {e}")
            return self._get_default_result()
    
    def _parse_text_response(self, response: str) -> Dict[str, Any]:
        """Parse text response when JSON parsing fails."""
        result = self._get_default_result()
        
        # Simple keyword-based parsing
        response_lower = response.lower()
        
        if 'hld' in response_lower or 'high' in response_lower:
            result['level'] = 'HLD'
        elif 'lld' in response_lower or 'low' in response_lower:
            result['level'] = 'LLD'
        
        if 'api' in response_lower:
            result['component_type'] = 'API'
        elif 'service' in response_lower:
            result['component_type'] = 'Service'
        elif 'function' in response_lower:
            result['component_type'] = 'Function'
        elif 'class' in response_lower:
            result['component_type'] = 'Class'
        
        return result
    
    def _normalize_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize and validate the analysis result."""
        normalized = self._get_default_result()
        
        # Copy valid fields
        if 'purpose' in result:
            normalized['purpose'] = str(result['purpose'])
        if 'level' in result and result['level'] in ['HLD', 'LLD']:
            normalized['level'] = result['level']
        if 'component_type' in result:
            normalized['component_type'] = str(result['component_type'])
        if 'complexity' in result and result['complexity'] in ['low', 'medium', 'high']:
            normalized['complexity'] = result['complexity']
        if 'relationships' in result and isinstance(result['relationships'], list):
            normalized['relationships'] = result['relationships']
        if 'confidence' in result:
            try:
                confidence = float(result['confidence'])
                normalized['confidence'] = max(0.0, min(1.0, confidence))
            except:
                pass
        
        return normalized
    
    def _get_default_result(self) -> Dict[str, Any]:
        """Get default analysis result."""
        return {
            'purpose': 'Code component',
            'level': 'LLD',
            'component_type': 'Function',
            'complexity': 'low',
            'relationships': [],
            'confidence': 0.5,
            'analysis_method': 'llm'
        }
    
    def _fallback_analysis(self, file_path: str, symbols: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback analysis when LLM is not available."""
        result = self._get_default_result()
        result['analysis_method'] = 'fallback'
        
        # Simple rule-based analysis
        file_name = Path(file_path).name.lower()
        file_path_lower = str(file_path).lower()
        
        # Check for HLD components
        if any(keyword in file_name for keyword in ['api', 'route', 'endpoint', 'controller']):
            result['level'] = 'HLD'
            result['component_type'] = 'API'
            result['purpose'] = 'Handles HTTP requests and API endpoints'
            result['complexity'] = 'medium'
        elif any(keyword in file_name for keyword in ['service', 'business', 'manager']):
            result['level'] = 'HLD'
            result['component_type'] = 'Service'
            result['purpose'] = 'Contains business logic and service operations'
            result['complexity'] = 'medium'
        elif any(keyword in file_name for keyword in ['app', 'main', 'server']):
            result['level'] = 'HLD'
            result['component_type'] = 'Application'
            result['purpose'] = 'Main application entry point and configuration'
            result['complexity'] = 'high'
        elif any(keyword in file_path_lower for keyword in ['/api/', '/routes/', '/controllers/']):
            result['level'] = 'HLD'
            result['component_type'] = 'API'
            result['purpose'] = 'API layer component'
            result['complexity'] = 'medium'
        elif any(keyword in file_path_lower for keyword in ['/services/', '/business/']):
            result['level'] = 'HLD'
            result['component_type'] = 'Service'
            result['purpose'] = 'Business logic service'
            result['complexity'] = 'medium'
        # Check for LLD components
        elif any(keyword in file_name for keyword in ['model', 'entity', 'schema']):
            result['level'] = 'LLD'
            result['component_type'] = 'Model'
            result['purpose'] = 'Defines data models and entities'
            result['complexity'] = 'low'
        elif any(keyword in file_name for keyword in ['util', 'helper', 'tool']):
            result['level'] = 'LLD'
            result['component_type'] = 'Utility'
            result['purpose'] = 'Utility functions and helper methods'
            result['complexity'] = 'low'
        elif any(keyword in file_name for keyword in ['test', 'spec']):
            result['level'] = 'LLD'
            result['component_type'] = 'Test'
            result['purpose'] = 'Test cases and specifications'
            result['complexity'] = 'low'
        elif any(keyword in file_path_lower for keyword in ['/models/', '/entities/']):
            result['level'] = 'LLD'
            result['component_type'] = 'Model'
            result['purpose'] = 'Data model component'
            result['complexity'] = 'low'
        elif any(keyword in file_path_lower for keyword in ['/utils/', '/helpers/']):
            result['level'] = 'LLD'
            result['component_type'] = 'Utility'
            result['purpose'] = 'Utility component'
            result['complexity'] = 'low'
        else:
            # Default analysis based on symbols
            if symbols.get('classes'):
                result['level'] = 'LLD'
                result['component_type'] = 'Class'
                result['purpose'] = 'Class definitions and implementations'
                result['complexity'] = 'medium'
            elif symbols.get('functions'):
                result['level'] = 'LLD'
                result['component_type'] = 'Function'
                result['purpose'] = 'Function implementations'
                result['complexity'] = 'low'
            else:
                result['level'] = 'LLD'
                result['component_type'] = 'File'
                result['purpose'] = 'Code file with various components'
                result['complexity'] = 'low'
        
        return result
    
    def _generate_cache_key(self, file_path: str, file_content: str, symbols: Dict[str, Any]) -> str:
        """Generate a cache key for the analysis."""
        content_hash = hashlib.md5(file_content.encode()).hexdigest()
        
        # Convert symbols to serializable format
        serializable_symbols = {}
        for key, value in symbols.items():
            if isinstance(value, list):
                serializable_symbols[key] = [str(item) if hasattr(item, 'name') else str(item) for item in value]
            else:
                serializable_symbols[key] = str(value)
        
        symbols_hash = hashlib.md5(json.dumps(serializable_symbols, sort_keys=True).encode()).hexdigest()
        return f"{Path(file_path).stem}_{content_hash[:8]}_{symbols_hash[:8]}" 