"""
HuggingFace Service
Fetches model information and benchmarks from HuggingFace model hub
"""

import re
import json
import requests
from typing import Dict, Optional, List, Any
from pathlib import Path


class HuggingFaceService:
    """Service for fetching and processing HuggingFace model data"""
    
    def __init__(self):
        self.api_base = "https://huggingface.co"
        self.mapping_config = self._load_mapping_config()
    
    def _load_mapping_config(self) -> dict:
        """Load RCA benchmark mapping configuration"""
        config_path = Path(__file__).parent.parent.parent / "data" / "rca_benchmark_mapping.json"
        with open(config_path, 'r') as f:
            return json.load(f)
    
    def parse_huggingface_url(self, url: str) -> Optional[str]:
        """
        Extract model ID from HuggingFace URL
        Examples:
        - https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro -> deepseek-ai/DeepSeek-V4-Pro
        - deepseek-ai/DeepSeek-V4-Pro -> deepseek-ai/DeepSeek-V4-Pro
        """
        # Remove trailing slashes
        url = url.rstrip('/')
        
        # If it's already just the model ID
        if '/' in url and 'huggingface.co' not in url:
            return url
        
        # Extract from full URL
        pattern = r'huggingface\.co/([^/]+/[^/]+)'
        match = re.search(pattern, url)
        if match:
            return match.group(1)
        
        return None
    
    def fetch_model_card(self, model_id: str) -> Optional[str]:
        """Fetch model card (README) from HuggingFace"""
        try:
            url = f"{self.api_base}/{model_id}/raw/main/README.md"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return response.text
            return None
        except Exception as e:
            print(f"Error fetching model card: {e}")
            return None
    
    def fetch_model_info(self, model_id: str, expand_eval_results: bool = True) -> Optional[Dict]:
        """
        Fetch model metadata from HuggingFace API
        
        Args:
            model_id: The model identifier (e.g., 'meta-llama/Llama-3.1-8B-Instruct')
            expand_eval_results: If True, includes evaluation results in the response
        
        Returns:
            Model metadata including eval_results if available
        """
        try:
            url = f"https://huggingface.co/api/models/{model_id}"
            
            # Add expand parameter to get evaluation results
            if expand_eval_results:
                url += "?expand[]=evalResults"
            
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"Error fetching model info: {e}")
            return None
    
    def fetch_from_open_llm_leaderboard(self, model_id: str) -> Dict[str, float]:
        """
        Fetch benchmark scores from Open LLM Leaderboard
        Uses the official leaderboard results dataset
        """
        benchmarks = {}
        try:
            # Use the HuggingFace datasets API to query leaderboard results
            # The Open LLM Leaderboard stores results in a dataset
            api_url = f"https://huggingface.co/api/datasets/open-llm-leaderboard/results/parquet/default/train/0.parquet"
            
            # Alternative: Try the results viewer API
            results_url = f"https://huggingface.co/datasets/open-llm-leaderboard/results/resolve/main/{model_id}/results*.json"
            
            # Try direct model results file
            model_results_url = f"https://huggingface.co/datasets/open-llm-leaderboard/results/resolve/main/{model_id.replace('/', '--')}/results_*.json"
            
            response = requests.get(model_results_url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract benchmark scores from results
                if 'results' in data:
                    results = data['results']
                    
                    # Map task names to our benchmark names
                    task_mapping = {
                        'mmlu': 'MMLU',
                        'arc_challenge': 'ARC',
                        'hellaswag': 'HellaSwag',
                        'truthfulqa_mc2': 'TruthfulQA',
                        'winogrande': 'Winogrande',
                        'gsm8k': 'GSM8K',
                        'humaneval': 'HumanEval',
                    }
                    
                    for task_key, benchmark_name in task_mapping.items():
                        if task_key in results:
                            # Results are usually in format: {task: {metric: value}}
                            task_data = results[task_key]
                            if isinstance(task_data, dict):
                                # Try common metric names
                                for metric in ['acc', 'acc_norm', 'exact_match', 'pass@1']:
                                    if metric in task_data:
                                        # Convert to 0-100 scale
                                        score = float(task_data[metric])
                                        if score <= 1.0:
                                            score *= 100
                                        benchmarks[benchmark_name] = score
                                        break
                            elif isinstance(task_data, (int, float)):
                                score = float(task_data)
                                if score <= 1.0:
                                    score *= 100
                                benchmarks[benchmark_name] = score
                                
        except Exception as e:
            print(f"Error fetching from Open LLM Leaderboard: {e}")
        
        return benchmarks
    
    def extract_benchmarks_from_model_data(self, model_data: Dict) -> Dict[str, float]:
        """
        Extract benchmarks from HuggingFace model API data
        Uses the official evalResults from expand parameter
        
        Actual format from API with expand=["evalResults"]:
        {
            "evalResults": [
                {
                    "data": {
                        "dataset": {"id": "openai/gsm8k", "task_id": "gsm8k"},
                        "value": 84.5
                    }
                },
                ...
            ]
        }
        """
        benchmarks = {}
        
        # OFFICIAL METHOD: Check evalResults from expand parameter
        if 'evalResults' in model_data and model_data['evalResults']:
            print(f"Found {len(model_data['evalResults'])} evaluation results")
            
            for result in model_data['evalResults']:
                # The actual structure has nested 'data' object
                if 'data' not in result:
                    continue
                    
                data = result['data']
                
                # Extract dataset ID from nested structure
                dataset_info = data.get('dataset', {})
                dataset_id = dataset_info.get('id', '').lower()
                task_id = dataset_info.get('task_id', '').lower()
                
                # Get the value
                value = data.get('value', 0)
                
                # Convert to 0-100 scale if needed
                score = float(value)
                if score <= 1.0:
                    score *= 100
                
                print(f"  Processing: dataset_id='{dataset_id}', task_id='{task_id}', value={score}")
                
                # Map dataset IDs to our benchmark names
                # Check both dataset_id and task_id for matches
                combined = f"{dataset_id} {task_id}"
                
                if 'humaneval' in combined:
                    benchmarks['HumanEval'] = score
                    print(f"    → Mapped to HumanEval")
                elif 'mmlu' in combined:
                    benchmarks['MMLU'] = score
                    print(f"    → Mapped to MMLU")
                elif 'gsm8k' in combined or 'gsm-8k' in combined:
                    benchmarks['GSM8K'] = score
                    print(f"    → Mapped to GSM8K")
                elif 'bbh' in combined or 'big-bench' in combined:
                    benchmarks['BBH'] = score
                    print(f"    → Mapped to BBH")
                elif 'arc' in combined:
                    benchmarks['ARC'] = score
                    print(f"    → Mapped to ARC")
                elif 'hellaswag' in combined:
                    benchmarks['HellaSwag'] = score
                    print(f"    → Mapped to HellaSwag")
                elif 'drop' in combined:
                    benchmarks['DROP'] = score
                    print(f"    → Mapped to DROP")
                elif 'truthfulqa' in combined:
                    benchmarks['TruthfulQA'] = score
                    print(f"    → Mapped to TruthfulQA")
                elif 'winogrande' in combined:
                    benchmarks['Winogrande'] = score
                    print(f"    → Mapped to Winogrande")
                elif 'mbpp' in combined:
                    benchmarks['MBPP'] = score
                    print(f"    → Mapped to MBPP")
                elif 'math' in combined:
                    benchmarks['MATH'] = score
                    print(f"    → Mapped to MATH")
                elif 'squad' in combined:
                    benchmarks['SQuAD'] = score
                    print(f"    → Mapped to SQuAD")
                elif 'boolq' in combined:
                    benchmarks['BoolQ'] = score
                    print(f"    → Mapped to BoolQ")
                elif 'gpqa' in combined:
                    benchmarks['GPQA'] = score
                    print(f"    → Mapped to GPQA")
                else:
                    print(f"    ⚠ No mapping found for this benchmark")
        
        # FALLBACK: Check legacy eval_results format (older API)
        if not benchmarks and 'eval_results' in model_data:
            for result in model_data['eval_results']:
                metric_name = result.get('metric_name', '')
                metric_value = result.get('metric_value', 0)
                
                # Map common metric names to our benchmarks
                if 'humaneval' in metric_name.lower():
                    benchmarks['HumanEval'] = float(metric_value)
                elif 'mmlu' in metric_name.lower():
                    benchmarks['MMLU'] = float(metric_value)
                elif 'gsm8k' in metric_name.lower():
                    benchmarks['GSM8K'] = float(metric_value)
                elif 'bbh' in metric_name.lower():
                    benchmarks['BBH'] = float(metric_value)
                elif 'arc' in metric_name.lower():
                    benchmarks['ARC'] = float(metric_value)
                elif 'hellaswag' in metric_name.lower():
                    benchmarks['HellaSwag'] = float(metric_value)
        
        # FALLBACK: Also check model-index in card data
        if not benchmarks and 'cardData' in model_data and model_data['cardData']:
            card_data = model_data['cardData']
            if 'model-index' in card_data:
                for model_entry in card_data['model-index']:
                    if 'results' in model_entry:
                        for result in model_entry['results']:
                            if 'metrics' in result:
                                for metric in result['metrics']:
                                    name = metric.get('name', '').lower()
                                    value = metric.get('value', 0)
                                    
                                    if 'humaneval' in name or 'pass@1' in name:
                                        benchmarks['HumanEval'] = float(value)
                                    elif 'mmlu' in name:
                                        benchmarks['MMLU'] = float(value)
                                    elif 'gsm8k' in name or 'gsm-8k' in name:
                                        benchmarks['GSM8K'] = float(value)
                                    elif 'bbh' in name or 'big-bench' in name:
                                        benchmarks['BBH'] = float(value)
                                    elif 'arc' in name:
                                        benchmarks['ARC'] = float(value)
                                    elif 'hellaswag' in name:
                                        benchmarks['HellaSwag'] = float(value)
        
        return benchmarks
    
    def extract_benchmarks(self, model_card: str) -> Dict[str, float]:
        """
        Extract benchmark scores from model card
        Looks for common patterns like:
        - HumanEval: 85.2
        - MMLU: 88.5%
        - GSM8K: 92.3
        """
        benchmarks = {}
        
        # Common benchmark patterns
        benchmark_names = [
            "HumanEval", "MBPP", "CodeContests",
            "MMLU", "BBH", "ARC", "HellaSwag",
            "GSM8K", "MATH", "DROP", "SQuAD",
            "BoolQ", "TruthfulQA", "Winogrande",
            "QuAC", "CoQA", "PIQA"
        ]
        
        for benchmark in benchmark_names:
            # Pattern: benchmark_name: score or benchmark_name score%
            patterns = [
                rf'{benchmark}[:\s]+(\d+\.?\d*)\s*%?',
                rf'{benchmark}[:\s]+(\d+\.?\d*)',
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, model_card, re.IGNORECASE)
                if matches:
                    try:
                        score = float(matches[0])
                        # Normalize to 0-100 scale
                        if score > 1:  # Already in percentage
                            benchmarks[benchmark] = min(score, 100)
                        else:  # In decimal form (0-1)
                            benchmarks[benchmark] = score * 100
                        break
                    except ValueError:
                        continue
        
        return benchmarks
    
    def calculate_task_score(self, task_name: str, benchmarks: Dict[str, float]) -> float:
        """
        Calculate RCA task score from available benchmarks
        Uses weighted average based on mapping configuration
        """
        task_config = self.mapping_config["rca_tasks"].get(task_name)
        if not task_config:
            return 50.0  # Default fallback
        
        total_weight = 0
        weighted_sum = 0
        
        for benchmark_info in task_config["benchmarks"]:
            benchmark_name = benchmark_info["name"]
            weight = benchmark_info["weight"]
            
            if benchmark_name in benchmarks:
                weighted_sum += benchmarks[benchmark_name] * weight
                total_weight += weight
        
        # If we have some benchmarks, calculate weighted average
        if total_weight > 0:
            score = weighted_sum / total_weight
            return round(score, 1)
        
        # No benchmarks found, use fallback
        return task_config["fallback_score"]
    
    def calculate_rca_scores(self, benchmarks: Dict[str, float]) -> Dict[str, float]:
        """Calculate all 8 RCA task scores from benchmarks"""
        rca_scores = {}
        
        for task_name in self.mapping_config["rca_tasks"].keys():
            rca_scores[task_name] = self.calculate_task_score(task_name, benchmarks)
        
        return rca_scores
    
    def calculate_overall_rca_score(self, task_scores: Dict[str, float]) -> float:
        """Calculate overall RCA score using task weights"""
        weights = self.mapping_config["overall_rca_weights"]
        
        total = sum(
            task_scores.get(task, 50) * weight
            for task, weight in weights.items()
        )
        
        return round(total, 1)
    
    def get_rca_assessment(self, rca_score: float) -> str:
        """Get qualitative assessment of RCA capability"""
        thresholds = self.mapping_config["rca_score_thresholds"]
        
        if rca_score >= thresholds["excellent"]:
            return "Excellent RCA capability"
        elif rca_score >= thresholds["good"]:
            return "Good RCA capability"
        elif rca_score >= thresholds["acceptable"]:
            return "Acceptable RCA capability"
        else:
            return "Needs improvement for RCA tasks"
    
    def detect_model_type(self, model_info: Dict) -> Dict[str, Any]:
        """
        Detect if model is suitable for RCA tasks or is for other purposes
        
        Returns:
            Dict with 'suitable': bool, 'model_type': str, 'reason': str
        """
        # Get model tags and pipeline tag
        tags = model_info.get('tags', [])
        pipeline_tag = model_info.get('pipeline_tag', '').lower()
        model_id = model_info.get('modelId', '').lower()
        
        # Non-suitable model types for RCA
        unsuitable_types = {
            'image': ['text-to-image', 'image-to-image', 'image-classification',
                     'object-detection', 'image-segmentation', 'depth-estimation',
                     'stable-diffusion', 'diffusion', 'imagen', 'dalle'],
            'video': ['text-to-video', 'video-classification', 'video-generation'],
            'audio': ['text-to-speech', 'automatic-speech-recognition', 'audio-classification',
                     'text-to-audio', 'audio-to-audio', 'whisper', 'wav2vec'],
            'multimodal': ['visual-question-answering', 'document-question-answering',
                          'image-to-text', 'zero-shot-image-classification', 'vision'],
            'other': ['reinforcement-learning', 'robotics', 'tabular-classification',
                     'time-series-forecasting']
        }
        
        # Check for multimodal models that are primarily vision-focused
        # These have text-generation pipeline but are designed for image/video understanding
        multimodal_vision_keywords = ['omni', 'vision', 'visual', 'vl-', 'vlm', 'multimodal',
                                      'image-text', 'video-text', 'clip', 'blip', 'flamingo']
        
        # If it's tagged as multimodal or has vision keywords, check if it's primarily for vision
        is_multimodal_vision = False
        if 'multimodal' in [t.lower() for t in tags]:
            # Check if model name/ID suggests it's vision-focused
            for keyword in multimodal_vision_keywords:
                if keyword in model_id:
                    is_multimodal_vision = True
                    break
        
        if is_multimodal_vision:
            return {
                'suitable': False,
                'model_type': 'multimodal_vision',
                'pipeline_tag': pipeline_tag or 'unknown',
                'reason': 'This is a multimodal vision model (handles images/video), not suitable for text-only RCA tasks.'
            }
        
        # Check pipeline tag
        for category, keywords in unsuitable_types.items():
            if pipeline_tag in keywords:
                return {
                    'suitable': False,
                    'model_type': category,
                    'pipeline_tag': pipeline_tag,
                    'reason': f'This is a {category} model ({pipeline_tag}), not suitable for RCA tasks which require text/code understanding.'
                }
        
        # Check tags
        for tag in tags:
            tag_lower = tag.lower()
            for category, keywords in unsuitable_types.items():
                if any(keyword in tag_lower for keyword in keywords):
                    return {
                        'suitable': False,
                        'model_type': category,
                        'pipeline_tag': pipeline_tag or 'unknown',
                        'reason': f'This is a {category} model, not suitable for RCA tasks which require text/code understanding.'
                    }
        
        # Check model ID for common patterns
        unsuitable_patterns = ['stable-diffusion', 'whisper', 'wav2vec', 'clip', 'vit',
                              'swin', 'dino', 'yolo', 'sam', 'segment-anything']
        for pattern in unsuitable_patterns:
            if pattern in model_id:
                return {
                    'suitable': False,
                    'model_type': 'specialized',
                    'pipeline_tag': pipeline_tag or 'unknown',
                    'reason': f'This model appears to be specialized for non-text tasks, not suitable for RCA.'
                }
        
        # Model is suitable for RCA
        return {
            'suitable': True,
            'model_type': 'text/code',
            'pipeline_tag': pipeline_tag or 'text-generation',
            'reason': 'Model is suitable for RCA tasks'
        }
    
    def process_huggingface_model(self, url: str) -> Dict:
        """
        Main method: Process HuggingFace URL and return RCA analysis
        Uses official HuggingFace API with expand=["evalResults"] for verified benchmark data
        """
        # Parse URL
        model_id = self.parse_huggingface_url(url)
        if not model_id:
            raise ValueError("Invalid HuggingFace URL")
        
        print(f"Processing model: {model_id}")
        
        # First, fetch basic model info WITHOUT expansion to get pipeline_tag for detection
        model_info_basic = self.fetch_model_info(model_id, expand_eval_results=False)
        if not model_info_basic:
            raise ValueError(f"Could not fetch model info for {model_id}")
        
        # Check if model is suitable for RCA tasks
        suitability = self.detect_model_type(model_info_basic)
        if not suitability['suitable']:
            print(f"⚠️ Model not suitable: {suitability['reason']}")
            return {
                "model_id": model_id,
                "name": model_info_basic.get("modelId", model_id).split("/")[-1],
                "provider": model_info_basic.get("modelId", model_id).split("/")[0],
                "suitable_for_rca": False,
                "model_type": suitability['model_type'],
                "pipeline_tag": suitability['pipeline_tag'],
                "rejection_reason": suitability['reason'],
                "message": "This model is not suitable for RCA tasks. Please select a text or code generation model."
            }
        
        # Model is suitable, now fetch WITH evalResults expansion for benchmarks
        model_info = self.fetch_model_info(model_id, expand_eval_results=True)
        if not model_info:
            # Fallback to basic info if expansion fails
            model_info = model_info_basic
        
        # Fetch model card for metadata extraction
        model_card = self.fetch_model_card(model_id)
        if not model_card:
            print(f"Warning: Could not fetch model card for {model_id}")
            model_card = ""
        
        # Try multiple sources for benchmarks - ONLY REAL DATA
        benchmarks = {}
        data_source = "none"
        
        # 1. PRIORITY: Official API evalResults (most reliable and verified)
        print("Attempting to extract benchmarks from official API evalResults...")
        benchmarks = self.extract_benchmarks_from_model_data(model_info)
        if benchmarks:
            data_source = "official_api"
            print(f"✓ Found {len(benchmarks)} benchmarks from official API")
        
        # 2. FALLBACK: Try Open LLM Leaderboard
        if not benchmarks:
            print("Attempting to fetch from Open LLM Leaderboard...")
            benchmarks = self.fetch_from_open_llm_leaderboard(model_id)
            if benchmarks:
                data_source = "open_llm_leaderboard"
                print(f"✓ Found {len(benchmarks)} benchmarks from Open LLM Leaderboard")
        
        # 3. FALLBACK: Try parsing the README
        if not benchmarks and model_card:
            print("Attempting to parse benchmarks from README...")
            benchmarks = self.extract_benchmarks(model_card)
            if benchmarks:
                data_source = "readme_parsing"
                print(f"✓ Found {len(benchmarks)} benchmarks from README")
        
        # NO ESTIMATION - If no real data found, warn user about low confidence
        if not benchmarks:
            print("⚠ No benchmark data found from any source")
            data_source = "none"
            
            # Extract model metadata for the warning response
            model_name = model_info.get("modelId", model_id).split("/")[-1]
            provider = model_info.get("modelId", model_id).split("/")[0]
            params = self._extract_parameters(model_card) if model_card else None
            context_window = self._extract_context_window(model_card) if model_card else None
            
            # Return low confidence warning instead of RCA scores
            return {
                "model_id": model_id,
                "name": model_name,
                "provider": provider,
                "version": "latest",
                "parameters": params or "Unknown",
                "context_window": context_window or 8192,
                "benchmarks": {},
                "benchmarks_found": 0,
                "data_source": "none",
                "confidence": "very_low",
                "warning": "No benchmark data available",
                "message": "Cannot calculate reliable RCA scores without benchmark data. Please use Manual Input mode to provide accurate scores.",
                "source": "huggingface"
            }
        
        # Calculate RCA scores (only if we have benchmarks)
        task_scores = self.calculate_rca_scores(benchmarks)
        overall_rca_score = self.calculate_overall_rca_score(task_scores)
        
        # Extract model metadata
        model_name = model_info.get("modelId", model_id).split("/")[-1]
        provider = model_info.get("modelId", model_id).split("/")[0]
        
        # Try to extract parameters and context window from card
        params = self._extract_parameters(model_card) if model_card else None
        context_window = self._extract_context_window(model_card) if model_card else None
        
        # Determine confidence level based on number of benchmarks
        confidence = "high" if len(benchmarks) >= 5 else "medium" if len(benchmarks) >= 2 else "low"
        
        return {
            "model_id": model_id,
            "name": model_name,
            "provider": provider,
            "version": "latest",
            "parameters": params or "Unknown",
            "context_window": context_window or 8192,
            "benchmarks": benchmarks,
            "task_scores": task_scores,
            "rca_score": overall_rca_score,
            "assessment": self.get_rca_assessment(overall_rca_score),
            "benchmarks_found": len(benchmarks),
            "data_source": data_source,
            "confidence": confidence,
            "source": "huggingface"
        }
    
    def _extract_parameters(self, model_card: str) -> Optional[str]:
        """Extract model parameter count from card"""
        patterns = [
            r'(\d+\.?\d*)\s*[BM]\s*parameters',
            r'(\d+\.?\d*)[BM]',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, model_card, re.IGNORECASE)
            if match:
                return match.group(0)
        
        return None
    
    def _extract_context_window(self, model_card: str) -> Optional[int]:
        """Extract context window size from card"""
        patterns = [
            r'context[:\s]+(\d+)k?',
            r'(\d+)k?\s*tokens?',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, model_card, re.IGNORECASE)
            if match:
                try:
                    value = int(match.group(1))
                    # If it's in thousands (e.g., "128k")
                    if 'k' in match.group(0).lower():
                        value *= 1000
                    return value
                except ValueError:
                    continue
        
        return None
    
    def _estimate_benchmarks_from_metadata(self, model_info: Dict, model_card: str) -> Dict[str, float]:
        """
        Estimate benchmark scores based on model metadata when no actual benchmarks are available
        This provides reasonable defaults based on model characteristics
        """
        benchmarks = {}
        base_score = 65  # Default for unknown models
        
        # Get model name for heuristics
        model_name = model_info.get('modelId', '').lower()
        
        # Extract parameter count
        params_str = self._extract_parameters(model_card) or ""
        
        # Estimate based on model size (rough heuristics)
        if 'B' in params_str.upper():
            try:
                param_count = float(params_str.upper().replace('B', '').strip())
                
                # Larger models generally perform better
                if param_count >= 100:  # 100B+ parameters
                    base_score = 75
                elif param_count >= 50:  # 50-100B
                    base_score = 70
                elif param_count >= 10:  # 10-50B
                    base_score = 65
                elif param_count >= 5:  # 5-10B
                    base_score = 60
                else:  # < 5B
                    base_score = 55
            except:
                pass
        
        # Use model name/version as fallback heuristic
        if not benchmarks:
            # Check for known high-performing model families
            if any(x in model_name for x in ['gpt-4', 'claude-3', 'deepseek-v3', 'deepseek-v4', 'llama-3-70b', 'mixtral-8x22b']):
                base_score = 75
            elif any(x in model_name for x in ['gpt-3.5', 'llama-3', 'llama-2-70b', 'mixtral', 'deepseek-v2']):
                base_score = 70
            elif any(x in model_name for x in ['llama-2', 'mistral', 'phi-3']):
                base_score = 65
            
            # Add some variation to make it realistic
            benchmarks = {
                'MMLU': float(base_score + 2),
                'HumanEval': float(base_score - 5),
                'GSM8K': float(base_score + 3),
                'BBH': float(base_score),
                'ARC': float(base_score + 1),
                'HellaSwag': float(base_score + 5),
            }
        
        return benchmarks


# Made with Bob