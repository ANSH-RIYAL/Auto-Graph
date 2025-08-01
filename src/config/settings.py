"""
Application settings and configuration management.
"""

import os
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
env_path = Path(__file__).parent.parent.parent / '.env'
if env_path.exists():
    load_dotenv(env_path)


class Settings:
    """Application settings loaded from environment variables."""
    
    # OpenAI Configuration
    OPENAI_API_KEY: Optional[str] = os.getenv('OPENAI_API_KEY')
    OPENAI_MODEL: str = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
    
    # LLM Analysis Configuration
    LLM_ENABLED: bool = os.getenv('LLM_ENABLED', 'true').lower() == 'true'
    LLM_CACHE_ENABLED: bool = os.getenv('LLM_CACHE_ENABLED', 'true').lower() == 'true'
    LLM_MAX_TOKENS: int = int(os.getenv('LLM_MAX_TOKENS', '2000'))
    LLM_TEMPERATURE: float = float(os.getenv('LLM_TEMPERATURE', '0.1'))
    
    # Quick disable for testing (set to 'false' to disable LLM calls completely)
    LLM_DISABLE_FOR_TESTING: bool = os.getenv('LLM_DISABLE_FOR_TESTING', 'true').lower() == 'true'
    
    @classmethod
    def validate_llm_config(cls) -> bool:
        """Validate that LLM configuration is complete."""
        if not cls.LLM_ENABLED or cls.LLM_DISABLE_FOR_TESTING:
            return False
        if not cls.OPENAI_API_KEY:
            return False
        return True
    
    @classmethod
    def get_llm_config(cls) -> dict:
        """Get LLM configuration as a dictionary."""
        return {
            'api_key': cls.OPENAI_API_KEY,
            'model': cls.OPENAI_MODEL,
            'max_tokens': cls.LLM_MAX_TOKENS,
            'temperature': cls.LLM_TEMPERATURE,
            'enabled': cls.LLM_ENABLED and not cls.LLM_DISABLE_FOR_TESTING,
            'cache_enabled': cls.LLM_CACHE_ENABLED,
            'disabled_for_testing': cls.LLM_DISABLE_FOR_TESTING
        }


# Global settings instance
settings = Settings() 