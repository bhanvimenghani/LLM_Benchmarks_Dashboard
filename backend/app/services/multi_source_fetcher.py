"""
Multi-Source Data Fetcher
Implements Vellum's approach: fetching from multiple sources for validation
"""

import requests
import json
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class BenchmarkScore:
    """Represents a benchmark score with metadata"""
    value: float
    source: str
    confidence: str  # 'high', 'medium', 'low'
    timestamp: str
    version: Optional[str] = None


@dataclass
class ModelData:
    """Complete model data from multiple sources"""
    id: str
    name: str
    provider: str
    version: str
    benchmarks: Dict[str, BenchmarkScore]
    metadata: Dict
    sources: List[str]
    last_updated: str
    confidence_score: float


class MultiSourceFetcher:
    """Fetch and aggregate data from multiple sources like Vellum"""
    
    def __init__(self):
        self.sources = {
            'huggingface': HuggingFaceSource(),
            'lmsys': LMSYSSource(),
            'openai': OpenAISource(),
            'anthropic': AnthropicSource(),
        }
        self.cache_file = "data/multi_source_cache.json"
        
    def fetch_model_data(self, model_id: str) -> Optional[ModelData]:
        """
        Fetch model data from all available sources and aggregate
        
        Args:
            model_id: Model identifier
            
        Returns:
            Aggregated ModelData with confidence scores
        """
        logger.info(f"Fetching data for {model_id} from multiple sources...")
        
        all_data = {}
        successful_sources = []
        
        # Fetch from each source
        for source_name, source in self.sources.items():
            try:
                data = source.fetch(model_id)
                if data:
                    all_data[source_name] = data
                    successful_sources.append(source_name)
                    logger.info(f"✓ Successfully fetched from {source_name}")
            except Exception as e:
                logger.warning(f"✗ Failed to fetch from {source_name}: {e}")
        
        if not all_data:
            logger.error(f"No data found for {model_id}")
            return None
        
        # Aggregate data from multiple sources
        aggregated = self._aggregate_data(model_id, all_data, successful_sources)
        return aggregated
    
    def fetch_all_models(self) -> List[ModelData]:
        """
        Fetch data for all available models from all sources
        
        Returns:
            List of ModelData objects
        """
        logger.info("Fetching all models from multiple sources...")
        
        # Get model list from HuggingFace (most comprehensive)
        hf_source = self.sources['huggingface']
        model_ids = hf_source.get_model_list()
        
        all_models = []
        for model_id in model_ids:
            model_data = self.fetch_model_data(model_id)
            if model_data:
                all_models.append(model_data)
            time.sleep(0.5)  # Rate limiting
        
        logger.info(f"Successfully fetched {len(all_models)} models")
        return all_models
    
    def _aggregate_data(
        self, 
        model_id: str, 
        all_data: Dict, 
        sources: List[str]
    ) -> ModelData:
        """
        Aggregate data from multiple sources with confidence scoring
        
        Args:
            model_id: Model identifier
            all_data: Data from all sources
            sources: List of successful sources
            
        Returns:
            Aggregated ModelData
        """
        # Extract basic info (prefer HuggingFace, then others)
        base_info = self._get_base_info(all_data, sources)
        
        # Aggregate benchmarks with multi-source validation
        benchmarks = self._aggregate_benchmarks(all_data)
        
        # Calculate overall confidence score
        confidence = self._calculate_confidence(benchmarks, len(sources))
        
        return ModelData(
            id=model_id,
            name=base_info['name'],
            provider=base_info['provider'],
            version=base_info['version'],
            benchmarks=benchmarks,
            metadata=base_info['metadata'],
            sources=sources,
            last_updated=datetime.utcnow().isoformat(),
            confidence_score=confidence
        )
    
    def _get_base_info(self, all_data: Dict, sources: List[str]) -> Dict:
        """Extract base model information"""
        # Priority: HuggingFace > OpenAI > Anthropic > LMSYS
        priority = ['huggingface', 'openai', 'anthropic', 'lmsys']
        
        for source in priority:
            if source in all_data:
                data = all_data[source]
                return {
                    'name': data.get('name', 'Unknown'),
                    'provider': data.get('provider', 'Unknown'),
                    'version': data.get('version', 'latest'),
                    'metadata': data.get('metadata', {})
                }
        
        # Fallback
        first_source = list(all_data.values())[0]
        return {
            'name': first_source.get('name', 'Unknown'),
            'provider': first_source.get('provider', 'Unknown'),
            'version': first_source.get('version', 'latest'),
            'metadata': first_source.get('metadata', {})
        }
    
    def _aggregate_benchmarks(self, all_data: Dict) -> Dict[str, BenchmarkScore]:
        """
        Aggregate benchmark scores from multiple sources
        Uses weighted average based on source reliability
        """
        # Source reliability weights
        source_weights = {
            'huggingface': 1.0,  # Most reliable
            'openai': 0.9,
            'anthropic': 0.9,
            'lmsys': 0.8
        }
        
        # Collect all benchmark scores
        benchmark_scores = {}
        
        for source_name, data in all_data.items():
            weight = source_weights.get(source_name, 0.5)
            benchmarks = data.get('benchmarks', {})
            
            for benchmark_name, score in benchmarks.items():
                if benchmark_name not in benchmark_scores:
                    benchmark_scores[benchmark_name] = []
                
                benchmark_scores[benchmark_name].append({
                    'value': score,
                    'source': source_name,
                    'weight': weight
                })
        
        # Calculate weighted averages
        aggregated = {}
        for benchmark_name, scores in benchmark_scores.items():
            if not scores:
                continue
            
            # Weighted average
            total_weight = sum(s['weight'] for s in scores)
            weighted_sum = sum(s['value'] * s['weight'] for s in scores)
            avg_score = weighted_sum / total_weight if total_weight > 0 else 0
            
            # Determine confidence based on number of sources
            num_sources = len(scores)
            if num_sources >= 3:
                confidence = 'high'
            elif num_sources == 2:
                confidence = 'medium'
            else:
                confidence = 'low'
            
            # Get primary source (highest weight)
            primary_source = max(scores, key=lambda x: x['weight'])['source']
            
            aggregated[benchmark_name] = BenchmarkScore(
                value=round(avg_score, 1),
                source=f"{num_sources} sources ({primary_source} primary)",
                confidence=confidence,
                timestamp=datetime.utcnow().isoformat(),
                version=None
            )
        
        return aggregated
    
    def _calculate_confidence(
        self, 
        benchmarks: Dict[str, BenchmarkScore], 
        num_sources: int
    ) -> float:
        """
        Calculate overall confidence score (0-100)
        Based on number of sources and benchmark confidence
        """
        if not benchmarks:
            return 0.0
        
        # Source diversity score (0-40 points)
        source_score = min(num_sources * 10, 40)
        
        # Benchmark confidence score (0-60 points)
        confidence_map = {'high': 60, 'medium': 40, 'low': 20}
        benchmark_scores = [
            confidence_map.get(b.confidence, 0) 
            for b in benchmarks.values()
        ]
        avg_benchmark_confidence = sum(benchmark_scores) / len(benchmark_scores)
        
        total_confidence = source_score + avg_benchmark_confidence
        return round(total_confidence, 1)


class HuggingFaceSource:
    """Fetch data from HuggingFace Open LLM Leaderboard"""
    
    def __init__(self):
        from .huggingface_live import HuggingFaceLiveFetcher
        self.live_fetcher = HuggingFaceLiveFetcher()
        
        # Known models mapping for ID translation
        self.known_models = {
            'gpt-4o': 'gpt-4o',
            'claude-3-5-sonnet': 'claude-3-5-sonnet',
            'gemini-1-5-pro': 'gemini-1-5-pro',
            'llama-3-1-405b': 'llama-3-1-405b',
            'llama-3-1-70b': 'llama-3-1-70b',
            'mistral-large-2': 'mistral-large-2',
        }
        self._cache = None
        self._cache_time = None
    
    def fetch(self, model_id: str) -> Optional[Dict]:
        """Fetch model data from HuggingFace"""
        try:
            # Get all models from live fetcher (with caching)
            all_models = self._get_cached_models()
            
            # Find the requested model
            for model in all_models:
                if model['model_id'] == model_id or model['model_name'].lower() == model_id.lower():
                    return {
                        'name': model['model_name'],
                        'provider': model['provider'],
                        'version': model.get('version', 'latest'),
                        'benchmarks': model.get('benchmarks', {}),
                        'metadata': model.get('metadata', {})
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching from HuggingFace: {e}")
            return None
    
    def _get_cached_models(self) -> List[Dict]:
        """Get models with 5-minute cache"""
        import time
        current_time = time.time()
        
        # Cache for 5 minutes
        if self._cache is None or (current_time - (self._cache_time or 0)) > 300:
            logger.info("Refreshing HuggingFace cache...")
            self._cache = self.live_fetcher.fetch_leaderboard_data()
            self._cache_time = current_time
        
        return self._cache
    
    def get_model_list(self) -> List[str]:
        """Get list of all available models"""
        try:
            all_models = self._get_cached_models()
            return [m['model_id'] for m in all_models]
        except Exception as e:
            logger.error(f"Error getting model list: {e}")
            return list(self.known_models.keys())


class LMSYSSource:
    """Fetch data from LMSYS Chatbot Arena"""
    
    def fetch(self, model_id: str) -> Optional[Dict]:
        """Fetch Elo ratings and human preferences"""
        # Mock implementation
        # In production, scrape or use LMSYS API
        return None


class OpenAISource:
    """Fetch metadata from OpenAI API"""
    
    def fetch(self, model_id: str) -> Optional[Dict]:
        """Fetch model metadata from OpenAI"""
        # Mock implementation
        # In production, use OpenAI API
        return None


class AnthropicSource:
    """Fetch metadata from Anthropic"""
    
    def fetch(self, model_id: str) -> Optional[Dict]:
        """Fetch model metadata from Anthropic"""
        # Mock implementation
        return None


# Example usage
if __name__ == "__main__":
    fetcher = MultiSourceFetcher()
    
    # Fetch single model
    model_data = fetcher.fetch_model_data('gpt-4o')
    if model_data:
        print(f"Model: {model_data.name}")
        print(f"Sources: {model_data.sources}")
        print(f"Confidence: {model_data.confidence_score}")
        print(f"Benchmarks: {len(model_data.benchmarks)}")
    
    # Fetch all models
    all_models = fetcher.fetch_all_models()
    print(f"\nTotal models fetched: {len(all_models)}")

# Made with Bob
