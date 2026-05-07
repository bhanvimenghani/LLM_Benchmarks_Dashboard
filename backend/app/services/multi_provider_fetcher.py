"""
Multi-Provider Model Fetcher
Aggregates models from HuggingFace, Google Gemini, and Anthropic Claude
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime
from .huggingface_live import HuggingFaceLiveFetcher
from .lmsys_live_fetcher import LMSYSLiveFetcher
# Note: Gemini and Claude services are optional and not currently implemented
# from .gemini_service import GeminiService
# from .claude_service import ClaudeService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MultiProviderFetcher:
    """
    Unified fetcher that aggregates models from multiple providers:
    - HuggingFace (open-source models)
    - Google Gemini (Google's AI models)
    - Anthropic Claude (Anthropic's AI models)
    """
    
    def __init__(self,
                 include_huggingface: bool = True,
                 include_lmsys: bool = True,
                 include_gemini: bool = False,
                 include_claude: bool = False):
        """
        Initialize multi-provider fetcher
        
        Args:
            include_huggingface: Include HuggingFace open-source models
            include_lmsys: Include LMSYS leaderboard (GPT, Claude, Gemini from Arena)
            include_gemini: Include Google Gemini models (fallback if LMSYS unavailable)
            include_claude: Include Anthropic Claude models (fallback if LMSYS unavailable)
        """
        self.include_huggingface = include_huggingface
        self.include_lmsys = include_lmsys
        self.include_gemini = include_gemini
        self.include_claude = include_claude
        
        # Initialize services
        self.hf_fetcher = HuggingFaceLiveFetcher() if include_huggingface else None
        self.lmsys_fetcher = LMSYSLiveFetcher() if include_lmsys else None
        # Gemini and Claude services are optional and not currently implemented
        self.gemini_service = None  # GeminiService() if include_gemini else None
        self.claude_service = None  # ClaudeService() if include_claude else None
        
    def fetch_all_models(self) -> List[Dict]:
        """
        Fetch models from all enabled providers
        
        Returns:
            List of models from all providers with standardized format
        """
        all_models = []
        fetch_summary = {
            'huggingface': 0,
            'lmsys': 0,
            'gemini': 0,
            'claude': 0,
            'total': 0
        }
        
        logger.info("=" * 80)
        logger.info("FETCHING MODELS FROM MULTIPLE PROVIDERS")
        logger.info("=" * 80)
        
        # Fetch from HuggingFace (open-source models)
        if self.include_huggingface and self.hf_fetcher:
            try:
                logger.info("\n[1/4] Fetching from HuggingFace Open LLM Leaderboard...")
                hf_models = self.hf_fetcher.fetch_leaderboard_data()
                
                # Add source tag to each model
                for model in hf_models:
                    model['source'] = 'huggingface'
                    if 'metadata' not in model:
                        model['metadata'] = {}
                    model['metadata']['provider_type'] = 'open-source'
                
                all_models.extend(hf_models)
                fetch_summary['huggingface'] = len(hf_models)
                logger.info(f"✓ Fetched {len(hf_models)} open-source models from HuggingFace")
            except Exception as e:
                logger.error(f"✗ Failed to fetch from HuggingFace: {e}")
        
        # Fetch from LMSYS (GPT, Claude, Gemini, and more)
        if self.include_lmsys and self.lmsys_fetcher:
            try:
                logger.info("\n[2/4] Fetching from LMSYS Chatbot Arena...")
                lmsys_models = self.lmsys_fetcher.fetch_lmsys_models()
                
                # Add source tag to each model
                for model in lmsys_models:
                    model['source'] = 'lmsys'
                    if 'metadata' not in model:
                        model['metadata'] = {}
                    model['metadata']['provider_type'] = 'proprietary'
                
                all_models.extend(lmsys_models)
                fetch_summary['lmsys'] = len(lmsys_models)
                logger.info(f"✓ Fetched {len(lmsys_models)} models from LMSYS (GPT, Claude, Gemini)")
            except Exception as e:
                logger.error(f"✗ Failed to fetch from LMSYS: {e}")
        
        # Fetch from Google Gemini (fallback if LMSYS didn't get them)
        # Note: Currently disabled - Gemini models are fetched via LMSYS
        if self.include_gemini and self.gemini_service:
            try:
                logger.info("\n[3/4] Fetching from Google Gemini (fallback)...")
                gemini_models = self.gemini_service.fetch_gemini_models()  # type: ignore
                
                if gemini_models:
                    # Add source tag to each model
                    for model in gemini_models:  # type: ignore
                        model['source'] = 'gemini'
                        if 'metadata' not in model:
                            model['metadata'] = {}
                        model['metadata']['provider_type'] = 'proprietary'
                    
                    all_models.extend(gemini_models)
                    fetch_summary['gemini'] = len(gemini_models)
                    logger.info(f"✓ Fetched {len(gemini_models)} models from Google Gemini")
            except Exception as e:
                logger.error(f"✗ Failed to fetch from Gemini: {e}")
        
        # Fetch from Anthropic Claude (fallback if LMSYS didn't get them)
        # Note: Currently disabled - Claude models are fetched via LMSYS
        if self.include_claude and self.claude_service:
            try:
                logger.info("\n[4/4] Fetching from Anthropic Claude (fallback)...")
                claude_models = self.claude_service.fetch_claude_models()  # type: ignore
                
                if claude_models:
                    # Add source tag to each model
                    for model in claude_models:  # type: ignore
                        model['source'] = 'claude'
                        if 'metadata' not in model:
                            model['metadata'] = {}
                        model['metadata']['provider_type'] = 'proprietary'
                    
                    all_models.extend(claude_models)
                    fetch_summary['claude'] = len(claude_models)
                    logger.info(f"✓ Fetched {len(claude_models)} models from Anthropic Claude")
            except Exception as e:
                logger.error(f"✗ Failed to fetch from Claude: {e}")
        
        fetch_summary['total'] = len(all_models)
        
        # Log summary
        logger.info("\n" + "=" * 80)
        logger.info("FETCH SUMMARY")
        logger.info("=" * 80)
        logger.info(f"HuggingFace (open-source): {fetch_summary['huggingface']} models")
        logger.info(f"LMSYS Arena (GPT/Claude/Gemini): {fetch_summary['lmsys']} models")
        logger.info(f"Google Gemini (fallback): {fetch_summary['gemini']} models")
        logger.info(f"Anthropic Claude (fallback): {fetch_summary['claude']} models")
        logger.info(f"TOTAL: {fetch_summary['total']} models")
        logger.info("=" * 80)
        
        return all_models
    
    def get_models_by_provider(self, provider: str) -> List[Dict]:
        """
        Get models from a specific provider
        
        Args:
            provider: Provider name ('huggingface', 'lmsys', 'gemini', 'claude')
            
        Returns:
            List of models from the specified provider
        """
        provider = provider.lower()
        
        if provider == 'huggingface' and self.hf_fetcher:
            models = self.hf_fetcher.fetch_leaderboard_data()
            for model in models:
                model['source'] = 'huggingface'
            return models
        
        elif provider == 'lmsys' and self.lmsys_fetcher:
            models = self.lmsys_fetcher.fetch_lmsys_models()
            for model in models:
                model['source'] = 'lmsys'
            return models
        
        elif provider == 'gemini' and self.gemini_service:
            # Note: Gemini service not currently implemented
            models = self.gemini_service.fetch_gemini_models()  # type: ignore
            if models:
                for model in models:  # type: ignore
                    model['source'] = 'gemini'
                return models
            return []
        
        elif provider == 'claude' and self.claude_service:
            # Note: Claude service not currently implemented
            models = self.claude_service.fetch_claude_models()  # type: ignore
            if models:
                for model in models:  # type: ignore
                    model['source'] = 'claude'
                return models
            return []
        
        else:
            raise ValueError(f"Unknown or disabled provider: {provider}")
    
    def get_provider_stats(self) -> Dict:
        """
        Get statistics about available providers
        
        Returns:
            Dictionary with provider statistics
        """
        return {
            'providers': {
                'huggingface': {
                    'enabled': self.include_huggingface,
                    'name': 'HuggingFace',
                    'type': 'open-source',
                    'description': 'Open-source models from HuggingFace leaderboard'
                },
                'gemini': {
                    'enabled': self.include_gemini,
                    'name': 'Google Gemini',
                    'type': 'proprietary',
                    'description': 'Google\'s Gemini AI models'
                },
                'claude': {
                    'enabled': self.include_claude,
                    'name': 'Anthropic Claude',
                    'type': 'proprietary',
                    'description': 'Anthropic\'s Claude AI models'
                }
            },
            'total_enabled': sum([
                self.include_huggingface,
                self.include_gemini,
                self.include_claude
            ])
        }


# Example usage
if __name__ == "__main__":
    # Fetch from all providers
    fetcher = MultiProviderFetcher(
        include_huggingface=True,
        include_gemini=True,
        include_claude=True
    )
    
    models = fetcher.fetch_all_models()
    
    print(f"\n✓ Total models fetched: {len(models)}")
    
    # Show sample from each provider
    print("\nSample models by provider:")
    for source in ['huggingface', 'gemini', 'claude']:
        source_models = [m for m in models if m.get('source') == source]
        if source_models:
            print(f"\n{source.upper()}:")
            for model in source_models[:3]:
                mmlu = model.get('benchmarks', {}).get('mmlu', 'N/A')
                print(f"  - {model['name']} ({model['provider']}): MMLU={mmlu}")

# Made with Bob
