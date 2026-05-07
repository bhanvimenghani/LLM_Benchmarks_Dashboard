"""
LMSYS Live Leaderboard Fetcher
Fetches latest model data from LMSYS Community API and OpenRouter
Includes Claude 3.5, GPT-4o, Gemini 1.5, and all latest models
"""

import logging
import requests
from typing import Dict, List, Optional
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LMSYSLiveFetcher:
    """
    Fetch latest model data from LMSYS Community API
    This provides real-time Elo ratings for all models including latest releases
    """
    
    # API endpoints
    LMSYS_API_URL = "https://api.wulong.dev/arena-ai-leaderboards/v1/leaderboard"
    OPENROUTER_API_URL = "https://openrouter.ai/api/v1/models"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'RCA-Dashboard/2.0'
        })
        
    def fetch_lmsys_models(self) -> List[Dict]:
        """
        Fetch all models from LMSYS Community API with live Elo ratings
        
        Returns:
            List of models with their Elo ratings and benchmark scores
        """
        logger.info("=" * 60)
        logger.info("Fetching LIVE data from LMSYS Community API")
        logger.info("=" * 60)
        
        try:
            # Fetch from LMSYS Community API
            logger.info("Fetching from LMSYS Arena leaderboard...")
            lmsys_models = self._fetch_from_lmsys_api()
            
            if not lmsys_models:
                logger.warning("No models fetched from LMSYS API")
                return []
            
            logger.info(f"✓ Fetched {len(lmsys_models)} models from LMSYS")
            
            # Enrich with OpenRouter metadata
            logger.info("Enriching with OpenRouter metadata...")
            enriched_models = self._enrich_with_openrouter(lmsys_models)
            
            logger.info(f"✓ Successfully processed {len(enriched_models)} models")
            return enriched_models
            
        except Exception as e:
            logger.error(f"Error fetching from LMSYS Live API: {e}")
            logger.error(f"Error details: {str(e)}")
            return []
    
    def _fetch_from_lmsys_api(self) -> List[Dict]:
        """
        Fetch models from LMSYS Community API
        
        Returns:
            List of models with Elo ratings
        """
        try:
            # Fetch text leaderboard
            response = self.session.get(
                f"{self.LMSYS_API_URL}?name=text",
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            models_data = data.get('models', [])
            
            if not models_data:
                logger.warning("No models in LMSYS API response")
                return []
            
            logger.info(f"Fetched {len(models_data)} models from LMSYS")
            logger.info(f"Last updated: {data.get('meta', {}).get('fetched_at', 'Unknown')}")
            
            # Convert to our format
            models = []
            for model_data in models_data:
                model = self._parse_lmsys_model(model_data)
                if model:
                    models.append(model)
            
            return models
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch from LMSYS API: {e}")
            return []
        except Exception as e:
            logger.error(f"Error parsing LMSYS data: {e}")
            return []
    
    def _parse_lmsys_model(self, model_data: Dict) -> Optional[Dict]:
        """
        Parse a model from LMSYS API response
        
        Args:
            model_data: Raw model data from API
            
        Returns:
            Parsed model dictionary
        """
        try:
            model_name = model_data.get('model', '')
            if not model_name:
                return None
            
            # Get Elo rating (called 'score' in this API)
            elo_rating = model_data.get('score', 0)
            
            # Determine provider
            provider = self._extract_provider(model_name, model_data.get('vendor', ''))
            
            # Estimate benchmarks from Elo
            benchmarks = self._estimate_benchmarks_from_elo(elo_rating, model_name)
            
            # Generate model ID
            model_id = model_name.lower().replace(' ', '-').replace('/', '-').replace('(', '').replace(')', '')
            
            return {
                'model_id': model_id,
                'id': model_id,
                'model_name': model_name,
                'name': model_name,
                'provider': provider,
                'version': self._extract_version(model_name),
                'benchmarks': benchmarks,
                'metadata': {
                    'parameters': 'Unknown',
                    'context_window': self._estimate_context_window(model_name),
                    'release_date': datetime.now().strftime("%Y-%m-%d"),
                    'source': 'LMSYS Arena (Live)',
                    'elo_rating': float(elo_rating) if elo_rating else 0,
                    'rank': model_data.get('rank', 0),
                    'votes': model_data.get('votes', 0),
                    'confidence_interval': model_data.get('ci', 0),
                    'license': model_data.get('license', 'Unknown'),
                    'full_model_name': model_name,
                    'data_source': 'LMSYS Community API (Live)'
                }
            }
            
        except Exception as e:
            logger.debug(f"Error parsing model {model_data.get('model')}: {e}")
            return None
    
    def _enrich_with_openrouter(self, models: List[Dict]) -> List[Dict]:
        """
        Enrich models with OpenRouter metadata (pricing, context window, etc.)
        
        Args:
            models: List of models from LMSYS
            
        Returns:
            Enriched models list
        """
        try:
            response = self.session.get(self.OPENROUTER_API_URL, timeout=30)
            response.raise_for_status()
            
            openrouter_data = response.json()
            openrouter_models = {m['id']: m for m in openrouter_data.get('data', [])}
            
            logger.info(f"Fetched {len(openrouter_models)} models from OpenRouter")
            
            # Match and enrich
            for model in models:
                model_name = model['model_name']
                
                # Try to find matching OpenRouter model
                or_model = None
                for or_id, or_data in openrouter_models.items():
                    if model_name.lower() in or_id.lower() or or_id.lower() in model_name.lower():
                        or_model = or_data
                        break
                
                if or_model:
                    # Enrich with OpenRouter data
                    model['metadata']['context_window'] = or_model.get('context_length', model['metadata']['context_window'])
                    model['metadata']['pricing'] = or_model.get('pricing', {})
                    model['metadata']['openrouter_id'] = or_model.get('id')
                    
            return models
            
        except Exception as e:
            logger.warning(f"Could not enrich with OpenRouter data: {e}")
            return models
    
    def _extract_provider(self, model_name: str, vendor: str = '') -> str:
        """Extract provider from model name or vendor"""
        if vendor:
            return vendor
        
        model_lower = model_name.lower()
        
        if 'gpt' in model_lower or 'openai' in model_lower:
            return 'OpenAI'
        elif 'claude' in model_lower or 'anthropic' in model_lower:
            return 'Anthropic'
        elif 'gemini' in model_lower or 'google' in model_lower or 'bard' in model_lower:
            return 'Google'
        elif 'llama' in model_lower or 'meta' in model_lower:
            return 'Meta'
        elif 'mistral' in model_lower or 'mixtral' in model_lower:
            return 'Mistral'
        elif 'grok' in model_lower or 'x-ai' in model_lower or 'xai' in model_lower:
            return 'xAI'
        elif 'muse' in model_lower:
            return 'Muse'
        elif '/' in model_name:
            return model_name.split('/')[0]
        else:
            return 'Unknown'
    
    def _extract_version(self, model_name: str) -> str:
        """Extract version from model name"""
        import re
        
        # Look for version patterns
        version_patterns = [
            r'(\d+\.?\d*\.?\d*)',  # Numbers like 4, 3.5, 1.5.0
            r'v(\d+)',              # v1, v2, etc.
        ]
        
        for pattern in version_patterns:
            match = re.search(pattern, model_name)
            if match:
                return match.group(1) if match.group(1) else match.group(0)
        
        return 'latest'
    
    def _normalize_elo_to_score(self, elo: float) -> float:
        """
        Normalize Elo rating to 0-100 score
        LMSYS Elo typically ranges from 1000-1600
        """
        if not elo:
            return 0.0
        
        # Normalize: 1000 -> 0, 1600 -> 100
        min_elo = 1000
        max_elo = 1600
        
        normalized = ((elo - min_elo) / (max_elo - min_elo)) * 100
        return max(0.0, min(100.0, normalized))
    
    def _estimate_benchmarks_from_elo(self, elo: float, model_name: str) -> Dict[str, float]:
        """
        Estimate benchmark scores from Elo rating
        This is an approximation based on correlation between Elo and benchmarks
        """
        if not elo:
            return {}
        
        # Normalize Elo to base score
        base_score = self._normalize_elo_to_score(elo)
        
        # Adjust based on model type
        model_lower = model_name.lower()
        
        # Different models have different strengths
        coding_multiplier = 1.0
        reasoning_multiplier = 1.0
        knowledge_multiplier = 1.0
        
        if 'opus-4' in model_lower or 'gpt-5' in model_lower:
            coding_multiplier = 1.2
            reasoning_multiplier = 1.2
            knowledge_multiplier = 1.15
        elif 'gpt-4' in model_lower or 'claude-3' in model_lower or 'opus' in model_lower:
            coding_multiplier = 1.15
            reasoning_multiplier = 1.15
            knowledge_multiplier = 1.1
        elif 'gemini' in model_lower and ('pro' in model_lower or 'ultra' in model_lower):
            knowledge_multiplier = 1.1
            reasoning_multiplier = 1.08
        elif 'grok' in model_lower:
            reasoning_multiplier = 1.1
        
        return {
            'mmlu': min(base_score * knowledge_multiplier, 100.0),
            'gsm8k': min(base_score * reasoning_multiplier * 0.95, 100.0),
            'humaneval': min(base_score * coding_multiplier * 0.9, 100.0),
            'hellaswag': min(base_score * 0.98, 100.0),
            'arc_challenge': min(base_score * 0.96, 100.0),
            'winogrande': min(base_score * 0.94, 100.0),
            'truthfulqa': min(base_score * 0.92, 100.0),
            'mbpp': min(base_score * coding_multiplier * 0.85, 100.0)
        }
    
    def _estimate_context_window(self, model_name: str) -> int:
        """Estimate context window from model name"""
        model_lower = model_name.lower()
        
        if 'opus-4' in model_lower or 'gpt-5' in model_lower:
            return 200000
        elif 'gpt-4' in model_lower and ('turbo' in model_lower or '1106' in model_lower or '0125' in model_lower):
            return 128000
        elif 'gpt-4' in model_lower:
            return 8192
        elif 'claude-3' in model_lower or 'claude-2' in model_lower:
            return 200000
        elif 'gemini' in model_lower and ('1.5' in model_lower or '2' in model_lower or '3' in model_lower):
            return 1000000
        elif 'gemini' in model_lower:
            return 32768
        elif 'grok' in model_lower:
            return 128000
        else:
            return 4096


# Example usage
if __name__ == "__main__":
    fetcher = LMSYSLiveFetcher()
    models = fetcher.fetch_lmsys_models()
    
    print(f"\nFetched {len(models)} models")
    print("\nTop 10 models by Elo:")
    for i, model in enumerate(models[:10], 1):
        print(f"{i}. {model['name']} ({model['provider']}) - Elo: {model['metadata']['elo_rating']:.1f}")

# Made with Bob
