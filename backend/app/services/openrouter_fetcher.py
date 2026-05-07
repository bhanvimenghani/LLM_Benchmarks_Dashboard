"""
OpenRouter Pricing and Performance Fetcher
Gets real-time pricing and operational data for models
Critical for RCA: logs are LONG, so cost matters
"""

import logging
import requests
from typing import Dict, Optional, List
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OpenRouterFetcher:
    """
    Fetch real-time pricing and performance data from OpenRouter
    """
    
    API_URL = "https://openrouter.ai/api/v1/models"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'RCA-Dashboard/2.0'
        })
        self.cache: Dict[str, Dict] = {}
        self.cache_time: Optional[datetime] = None
    
    def fetch_all_models(self) -> Dict[str, Dict]:
        """
        Fetch all models with pricing and performance data
        
        Returns:
            Dict mapping model IDs to their operational data
        """
        logger.info("=" * 60)
        logger.info("Fetching OpenRouter Pricing & Performance Data")
        logger.info("=" * 60)
        
        try:
            response = self.session.get(self.API_URL, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            models = data.get('data', [])
            
            logger.info(f"✓ Fetched data for {len(models)} models from OpenRouter")
            
            # Parse and structure the data
            structured_data = {}
            for model in models:
                model_id = model.get('id', '')
                structured_data[model_id] = self._parse_model_data(model)
            
            self.cache = structured_data
            self.cache_time = datetime.utcnow()
            
            return structured_data
            
        except Exception as e:
            logger.error(f"Error fetching from OpenRouter: {e}")
            return self._get_fallback_data()
    
    def _parse_model_data(self, model: Dict) -> Dict:
        """
        Parse OpenRouter model data into our format
        """
        pricing = model.get('pricing', {})
        
        # Convert to cost per 1M tokens
        prompt_cost = float(pricing.get('prompt', '0')) * 1_000_000
        completion_cost = float(pricing.get('completion', '0')) * 1_000_000
        
        # Calculate cost per 1k logs (assuming avg log is 2k tokens)
        cost_per_1k_logs = (prompt_cost * 2000 + completion_cost * 500) / 1_000_000
        
        return {
            'model_id': model.get('id'),
            'name': model.get('name'),
            'context_length': model.get('context_length', 0),
            'pricing': {
                'prompt_per_1m': round(prompt_cost, 2),
                'completion_per_1m': round(completion_cost, 2),
                'cost_per_1k_logs': round(cost_per_1k_logs, 2)
            },
            'architecture': model.get('architecture', {}),
            'top_provider': model.get('top_provider', {}),
            'per_request_limits': model.get('per_request_limits')
        }
    
    def get_model_pricing(self, model_id: str) -> Optional[Dict]:
        """
        Get pricing for a specific model
        """
        if not self.cache or len(self.cache) == 0:
            self.fetch_all_models()
        
        return self.cache.get(model_id) if self.cache else None
    
    def calculate_rca_cost(self, model_id: str, avg_log_tokens: int = 2000) -> float:
        """
        Calculate estimated cost for RCA analysis
        
        Args:
            model_id: Model identifier
            avg_log_tokens: Average tokens in a log file (default: 2000)
        
        Returns:
            Estimated cost in USD
        """
        model_data = self.get_model_pricing(model_id)
        if not model_data:
            return 0.0
        
        pricing = model_data['pricing']
        
        # Assume: 2k tokens input (logs), 500 tokens output (analysis)
        input_cost = (avg_log_tokens / 1_000_000) * pricing['prompt_per_1m']
        output_cost = (500 / 1_000_000) * pricing['completion_per_1m']
        
        return round(input_cost + output_cost, 4)
    
    def _get_fallback_data(self) -> Dict[str, Dict]:
        """
        Fallback data if OpenRouter API is unavailable
        Based on known pricing as of 2024
        """
        logger.warning("Using fallback pricing data")
        
        return {
            'anthropic/claude-3.5-sonnet': {
                'model_id': 'anthropic/claude-3.5-sonnet',
                'name': 'Claude 3.5 Sonnet',
                'context_length': 200000,
                'pricing': {
                    'prompt_per_1m': 3.00,
                    'completion_per_1m': 15.00,
                    'cost_per_1k_logs': 0.0135
                }
            },
            'anthropic/claude-3-opus': {
                'model_id': 'anthropic/claude-3-opus',
                'name': 'Claude 3 Opus',
                'context_length': 200000,
                'pricing': {
                    'prompt_per_1m': 15.00,
                    'completion_per_1m': 75.00,
                    'cost_per_1k_logs': 0.0675
                }
            },
            'openai/gpt-4o': {
                'model_id': 'openai/gpt-4o',
                'name': 'GPT-4o',
                'context_length': 128000,
                'pricing': {
                    'prompt_per_1m': 5.00,
                    'completion_per_1m': 15.00,
                    'cost_per_1k_logs': 0.0175
                }
            },
            'openai/gpt-4-turbo': {
                'model_id': 'openai/gpt-4-turbo',
                'name': 'GPT-4 Turbo',
                'context_length': 128000,
                'pricing': {
                    'prompt_per_1m': 10.00,
                    'completion_per_1m': 30.00,
                    'cost_per_1k_logs': 0.035
                }
            },
            'google/gemini-pro-1.5': {
                'model_id': 'google/gemini-pro-1.5',
                'name': 'Gemini 1.5 Pro',
                'context_length': 1000000,
                'pricing': {
                    'prompt_per_1m': 3.50,
                    'completion_per_1m': 10.50,
                    'cost_per_1k_logs': 0.0123
                }
            },
            'meta-llama/llama-3-70b-instruct': {
                'model_id': 'meta-llama/llama-3-70b-instruct',
                'name': 'Llama 3 70B Instruct',
                'context_length': 8192,
                'pricing': {
                    'prompt_per_1m': 0.59,
                    'completion_per_1m': 0.79,
                    'cost_per_1k_logs': 0.0016
                }
            },
            'mistralai/mixtral-8x22b-instruct': {
                'model_id': 'mistralai/mixtral-8x22b-instruct',
                'name': 'Mixtral 8x22B Instruct',
                'context_length': 65536,
                'pricing': {
                    'prompt_per_1m': 0.65,
                    'completion_per_1m': 0.65,
                    'cost_per_1k_logs': 0.0016
                }
            },
            'deepseek/deepseek-coder-v2': {
                'model_id': 'deepseek/deepseek-coder-v2',
                'name': 'DeepSeek Coder V2',
                'context_length': 128000,
                'pricing': {
                    'prompt_per_1m': 0.14,
                    'completion_per_1m': 0.28,
                    'cost_per_1k_logs': 0.0004
                }
            }
        }
    
    def get_top_models_by_cost_efficiency(self, limit: int = 10) -> List[Dict]:
        """
        Get models ranked by cost efficiency for RCA
        (Best reasoning score per dollar)
        """
        if not self.cache or len(self.cache) == 0:
            self.fetch_all_models()
        
        # This would be combined with reasoning scores in practice
        models_with_efficiency: List[Dict] = []
        
        for model_id, data in (self.cache or {}).items():
            cost = data['pricing']['cost_per_1k_logs']
            if cost > 0:
                models_with_efficiency.append({
                    'model_id': model_id,
                    'name': data['name'],
                    'cost': cost,
                    'context_length': data['context_length']
                })
        
        # Sort by cost (ascending)
        models_with_efficiency.sort(key=lambda x: x['cost'])
        
        return models_with_efficiency[:limit]


# Example usage
if __name__ == "__main__":
    fetcher = OpenRouterFetcher()
    
    # Fetch all models
    models = fetcher.fetch_all_models()
    
    print("\n" + "=" * 60)
    print("OPENROUTER PRICING DATA")
    print("=" * 60)
    
    # Show top 10 by cost efficiency
    print("\nTop 10 Most Cost-Efficient Models:")
    top_models = fetcher.get_top_models_by_cost_efficiency(10)
    
    for i, model in enumerate(top_models, 1):
        print(f"{i}. {model['name']}")
        print(f"   Cost per 1k logs: ${model['cost']:.4f}")
        print(f"   Context length: {model['context_length']:,} tokens")
        print()

# Made with Bob
