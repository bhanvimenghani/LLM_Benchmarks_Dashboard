"""
Reasoning Benchmark Fetcher - LIVE DATA ONLY
Fetches from actual live sources:
- SWE-bench: GitHub repository (swe-bench.github.io)
- BBH/MMLU: HuggingFace Open LLM Leaderboard
- GPQA: Artificial Analysis (with fallback)
"""

import logging
import requests
from typing import Dict, List, Optional
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ReasoningBenchmarkFetcher:
    """
    Fetch LIVE reasoning benchmarks from actual sources
    NO HARDCODED DATA - Everything is fetched in real-time
    """
    
    # Live data sources
    SWEBENCH_GITHUB_URL = "https://raw.githubusercontent.com/swe-bench/swe-bench.github.io/main/public/data/verified_leaderboard.json"
    HUGGINGFACE_LEADERBOARD_API = "https://huggingface.co/api/open-llm-leaderboard"
    ARTIFICIAL_ANALYSIS_URL = "https://artificialanalysis.ai/api/models"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'RCA-Dashboard/2.0 (Technical Leaderboard)'
        })
        self.cache: Dict[str, Dict] = {}
        
    def fetch_all_reasoning_scores(self) -> Dict[str, Dict]:
        """
        Fetch all reasoning benchmarks from LIVE sources
        
        Returns:
            Dict mapping model names to their reasoning scores
        """
        logger.info("=" * 80)
        logger.info("FETCHING LIVE REASONING BENCHMARKS (NO HARDCODED DATA)")
        logger.info("=" * 80)
        
        all_scores: Dict[str, Dict] = {}
        
        # 1. SWE-bench from GitHub (GOLD STANDARD for RCA)
        logger.info("\n[1/3] Fetching SWE-bench from GitHub repository...")
        swebench_scores = self.fetch_swebench_from_github()
        self._merge_scores(all_scores, swebench_scores, 'swebench')
        logger.info(f"      ✓ Got {len(swebench_scores)} models with SWE-bench scores")
        
        # 2. HuggingFace Open LLM Leaderboard (BBH, MMLU, etc.)
        logger.info("\n[2/3] Fetching from HuggingFace Open LLM Leaderboard...")
        hf_scores = self.fetch_huggingface_leaderboard()
        self._merge_scores(all_scores, hf_scores, 'hf_benchmarks')
        logger.info(f"      ✓ Got {len(hf_scores)} models with HF benchmark scores")
        
        # 3. GPQA from Artificial Analysis
        logger.info("\n[3/3] Fetching GPQA from Artificial Analysis...")
        gpqa_scores = self.fetch_gpqa_scores()
        self._merge_scores(all_scores, gpqa_scores, 'gpqa')
        logger.info(f"      ✓ Got {len(gpqa_scores)} models with GPQA scores")
        
        logger.info("\n" + "=" * 80)
        logger.info(f"TOTAL: Fetched reasoning data for {len(all_scores)} unique models")
        logger.info("=" * 80)
        
        return all_scores
    
    def fetch_swebench_from_github(self) -> Dict[str, float]:
        """
        Fetch SWE-bench scores from official GitHub repository
        This is the GOLD STANDARD for RCA capability
        
        Source: https://github.com/swe-bench/swe-bench.github.io
        
        Returns:
            Dict mapping model names to resolve rates (0-100)
        """
        try:
            # Try verified leaderboard first (curated, higher quality)
            urls_to_try = [
                "https://raw.githubusercontent.com/swe-bench/swe-bench.github.io/main/public/data/verified_leaderboard.json",
                "https://raw.githubusercontent.com/swe-bench/swe-bench.github.io/main/public/data/leaderboard.json",
                "https://raw.githubusercontent.com/swe-bench/experiments/main/evaluation/verified/20240620_sweagent_claude3.5sonnet/results.json"
            ]
            
            for url in urls_to_try:
                try:
                    logger.info(f"      Trying: {url}")
                    response = self.session.get(url, timeout=30)
                    response.raise_for_status()
                    
                    data = response.json()
                    scores = {}
                    
                    # Parse the leaderboard structure
                    if isinstance(data, list):
                        for entry in data:
                            model_name = entry.get('model', entry.get('name', '')).lower()
                            # Look for resolve rate or percentage
                            resolve_rate = entry.get('resolve_rate', entry.get('percentage', entry.get('score', 0)))
                            if model_name and resolve_rate:
                                scores[model_name] = float(resolve_rate)
                    elif isinstance(data, dict):
                        # Handle dict format
                        for model_name, model_data in data.items():
                            if isinstance(model_data, dict):
                                resolve_rate = model_data.get('resolve_rate', model_data.get('percentage', 0))
                                scores[model_name.lower()] = float(resolve_rate)
                            elif isinstance(model_data, (int, float)):
                                scores[model_name.lower()] = float(model_data)
                    
                    if scores:
                        logger.info(f"      ✓ Successfully parsed SWE-bench data")
                        return scores
                        
                except Exception as e:
                    logger.debug(f"      Failed to fetch from {url}: {e}")
                    continue
            
            logger.warning("      ⚠️ Could not fetch SWE-bench from any GitHub source")
            return {}
            
        except Exception as e:
            logger.error(f"      ✗ Error fetching SWE-bench: {e}")
            return {}
    
    def fetch_huggingface_leaderboard(self) -> Dict[str, Dict]:
        """
        Fetch benchmark scores from HuggingFace Open LLM Leaderboard
        Includes BBH, MMLU, and other reasoning benchmarks
        
        Returns:
            Dict mapping model names to benchmark scores
        """
        try:
            # HuggingFace Spaces API endpoint
            url = "https://huggingface.co/api/spaces/HuggingFaceH4/open_llm_leaderboard"
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            scores: Dict[str, Dict] = {}
            
            # Parse the leaderboard data
            # Structure varies, so we handle multiple formats
            if 'data' in data:
                for entry in data['data']:
                    model_name = entry.get('model', '').lower()
                    if model_name:
                        scores[model_name] = {
                            'mmlu': entry.get('MMLU', 0),
                            'bbh': entry.get('BBH', 0),
                            'math': entry.get('MATH', 0),
                            'gpqa': entry.get('GPQA', 0),
                            'average': entry.get('Average', 0)
                        }
            
            if scores:
                logger.info(f"      ✓ Successfully fetched HuggingFace leaderboard")
                return scores
            else:
                logger.warning("      ⚠️ No data from HuggingFace API")
                return {}
                
        except Exception as e:
            logger.error(f"      ✗ Error fetching HuggingFace leaderboard: {e}")
            return {}
    
    def fetch_gpqa_scores(self) -> Dict[str, float]:
        """
        Fetch GPQA scores from Artificial Analysis
        Graduate-level reasoning benchmark
        
        Returns:
            Dict mapping model names to GPQA scores (0-100)
        """
        try:
            # Try Artificial Analysis API
            url = "https://artificialanalysis.ai/api/models"
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            scores = {}
            
            # Parse the API response
            if isinstance(data, list):
                for model in data:
                    model_name = model.get('name', model.get('model', '')).lower()
                    gpqa_score = model.get('gpqa', model.get('gpqa_diamond', 0))
                    if model_name and gpqa_score:
                        scores[model_name] = float(gpqa_score)
            
            if scores:
                logger.info(f"      ✓ Successfully fetched GPQA scores")
                return scores
            else:
                logger.warning("      ⚠️ No GPQA data from Artificial Analysis")
                return {}
                
        except Exception as e:
            logger.error(f"      ✗ Error fetching GPQA scores: {e}")
            return {}
    
    def _merge_scores(self, all_scores: Dict, new_scores: Dict, score_type: str):
        """
        Merge new scores into the all_scores dictionary
        """
        for model_name, score in new_scores.items():
            if model_name not in all_scores:
                all_scores[model_name] = {}
            all_scores[model_name][score_type] = score
    
    def calculate_reasoning_composite(self, model_scores: Dict) -> Dict:
        """
        Calculate composite reasoning score from available benchmarks
        
        Weighting:
        - SWE-bench: 50% (most relevant to RCA)
        - HF Benchmarks (BBH/MMLU): 30%
        - GPQA: 20%
        
        Args:
            model_scores: Dict with benchmark scores
        
        Returns:
            Dict with composite score and confidence
        """
        scores = []
        weights = []
        
        # SWE-bench: Highest weight (most relevant to RCA)
        if 'swebench' in model_scores:
            scores.append(model_scores['swebench'])
            weights.append(0.50)
        
        # HuggingFace benchmarks: High weight
        if 'hf_benchmarks' in model_scores:
            hf_data = model_scores['hf_benchmarks']
            if isinstance(hf_data, dict):
                # Average of available HF benchmarks
                hf_scores = [v for v in hf_data.values() if isinstance(v, (int, float)) and v > 0]
                if hf_scores:
                    scores.append(sum(hf_scores) / len(hf_scores))
                    weights.append(0.30)
        
        # GPQA: Medium weight
        if 'gpqa' in model_scores:
            scores.append(model_scores['gpqa'])
            weights.append(0.20)
        
        if not scores:
            return {
                'composite_score': 0,
                'confidence': 'none',
                'sources_used': 0,
                'note': 'No live benchmark data available'
            }
        
        # Weighted average
        composite = sum(s * w for s, w in zip(scores, weights)) / sum(weights)
        
        # Confidence based on number of sources
        confidence = 'high' if len(scores) >= 3 else 'medium' if len(scores) == 2 else 'low'
        
        return {
            'composite_score': round(composite, 1),
            'confidence': confidence,
            'sources_used': len(scores),
            'breakdown': model_scores
        }


# Example usage and testing
if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("TESTING LIVE REASONING BENCHMARK FETCHER")
    print("=" * 80)
    
    fetcher = ReasoningBenchmarkFetcher()
    scores = fetcher.fetch_all_reasoning_scores()
    
    if scores:
        print(f"\n✓ Successfully fetched data for {len(scores)} models\n")
        
        # Show top 5 models
        print("Top 5 Models by Available Data:")
        print("-" * 80)
        
        for i, (model, model_scores) in enumerate(list(scores.items())[:5], 1):
            composite = fetcher.calculate_reasoning_composite(model_scores)
            print(f"\n{i}. {model}")
            print(f"   Composite Score: {composite['composite_score']}/100")
            print(f"   Confidence: {composite['confidence']}")
            print(f"   Sources: {composite['sources_used']}")
            print(f"   Data: {model_scores}")
    else:
        print("\n⚠️ No live data available")
        print("\nPossible reasons:")
        print("  - GitHub rate limiting")
        print("  - API endpoints changed")
        print("  - Network connectivity issues")
        print("\nRecommendation: Check the source URLs and update if needed")

# Made with Bob
