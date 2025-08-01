"""
Agent detector for AutoGraph.
Detects AI agent usage patterns in code files.
"""

import re
from typing import Dict, List, Any, Optional
from pathlib import Path
from ..utils.logger import get_logger

logger = get_logger(__name__)


class AgentDetector:
    """Detects AI agent usage patterns in code files."""
    
    def __init__(self):
        # Common AI agent libraries and patterns
        self.agent_patterns = {
            'openai': [
                r'openai\.ChatCompletion',
                r'openai\.Completion',
                r'openai\.OpenAI',
                r'gpt-4',
                r'gpt-3\.5',
                r'text-davinci'
            ],
            'langchain': [
                r'langchain',
                r'LLMChain',
                r'AgentExecutor',
                r'ConversationChain',
                r'PromptTemplate'
            ],
            'anthropic': [
                r'anthropic\.Client',
                r'claude',
                r'Claude'
            ],
            'custom': [
                r'agent',
                r'llm',
                r'ai_model',
                r'neural',
                r'machine_learning'
            ]
        }
    
    def detect_agent_usage(self, file_content: str, file_path: str) -> Dict[str, Any]:
        """Detect AI agent usage in a file."""
        logger.debug(f"Detecting agent usage in: {file_path}")
        
        detected_agents = {}
        total_matches = 0
        
        for agent_type, patterns in self.agent_patterns.items():
            matches = []
            for pattern in patterns:
                found = re.findall(pattern, file_content, re.IGNORECASE)
                if found:
                    matches.extend(found)
            
            if matches:
                detected_agents[agent_type] = {
                    'patterns_found': list(set(matches)),
                    'match_count': len(matches)
                }
                total_matches += len(matches)
        
        return {
            'has_agent': bool(detected_agents),
            'agent_types': list(detected_agents.keys()),
            'total_matches': total_matches,
            'detected_agents': detected_agents,
            'file_path': file_path
        }
    
    def analyze_agent_context(self, file_content: str, symbols: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the context of agent usage in a file."""
        # Extract functions and classes that might use agents
        functions = symbols.get('functions', [])
        classes = symbols.get('classes', [])
        
        # Look for agent usage in function/class definitions
        agent_functions = []
        agent_classes = []
        
        for func in functions:
            if self._contains_agent_usage(func, file_content):
                agent_functions.append(func)
        
        for cls in classes:
            if self._contains_agent_usage(cls, file_content):
                agent_classes.append(cls)
        
        return {
            'agent_functions': agent_functions,
            'agent_classes': agent_classes,
            'agent_context': self._extract_agent_context(file_content)
        }
    
    def _contains_agent_usage(self, symbol: str, file_content: str) -> bool:
        """Check if a symbol contains agent usage."""
        # Simple check - can be enhanced with more sophisticated analysis
        for patterns in self.agent_patterns.values():
            for pattern in patterns:
                if re.search(pattern, file_content, re.IGNORECASE):
                    return True
        return False
    
    def _extract_agent_context(self, file_content: str) -> str:
        """Extract context around agent usage."""
        # Find lines with agent usage
        lines = file_content.split('\n')
        agent_lines = []
        
        for i, line in enumerate(lines):
            for patterns in self.agent_patterns.values():
                for pattern in patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        # Get context (previous and next lines)
                        start = max(0, i - 2)
                        end = min(len(lines), i + 3)
                        context = lines[start:end]
                        agent_lines.extend(context)
                        break
        
        return '\n'.join(agent_lines) if agent_lines else "" 