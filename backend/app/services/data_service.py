"""
Data Service
Handles loading and processing model and task data
NOW USES LIVE HUGGINGFACE DATA - NO HARDCODING
"""

import json
from pathlib import Path
from typing import List, Dict, Optional
from ..models.schemas import Model, TaskLeaderboard, TaskInfo, ModelScore
from .huggingface_live import HuggingFaceLiveFetcher
from .multi_provider_fetcher import MultiProviderFetcher
from .rca_calculator import RCACalculator


class DataService:
    """Service for loading and managing model and task data"""
    
    USER_MODELS_FILE = "data/user_models.json"
    
    def __init__(self, data_file: str = "backend/data/models_tasks.json", use_real_data: bool = True, use_multi_provider: bool = True):
        """
        Initialize the data service
        
        Args:
            data_file: Path to the JSON data file (fallback)
            use_real_data: If True, fetch LIVE data from APIs (NO HARDCODING)
            use_multi_provider: If True, fetch from multiple providers (HuggingFace, Gemini, Claude)
        """
        self.data_file = Path(data_file)
        self.use_real_data = use_real_data
        self.use_multi_provider = use_multi_provider
        
        # Use multi-provider fetcher if enabled, otherwise use HuggingFace only
        if use_real_data:
            if use_multi_provider:
                self.live_fetcher = MultiProviderFetcher(
                    include_huggingface=True,
                    include_lmsys=True,  # LMSYS has GPT, Claude, Gemini
                    include_gemini=False,  # Fallback only
                    include_claude=False   # Fallback only
                )
            else:
                self.live_fetcher = HuggingFaceLiveFetcher()
        else:
            self.live_fetcher = None
            
        self.rca_calculator = RCACalculator()
        self.data = self._load_data()
    
    def _load_data(self) -> dict:
        """
        Load LIVE data from multiple provider APIs - NO HARDCODING
        Fetches fresh data from HuggingFace, Gemini, and Claude
        """
        if self.use_real_data and self.live_fetcher:
            try:
                # Fetch LIVE data from multiple providers
                if self.use_multi_provider and isinstance(self.live_fetcher, MultiProviderFetcher):
                    print("🔴 FETCHING LIVE DATA FROM MULTIPLE PROVIDERS - NO HARDCODING")
                    print("   - HuggingFace (open-source models)")
                    print("   - Google Gemini (proprietary models)")
                    print("   - Anthropic Claude (proprietary models)")
                    models = self.live_fetcher.fetch_all_models()
                elif isinstance(self.live_fetcher, HuggingFaceLiveFetcher):
                    print("🔴 FETCHING LIVE DATA FROM HUGGINGFACE API - NO HARDCODING")
                    models = self.live_fetcher.fetch_leaderboard_data()
                else:
                    raise ValueError("Invalid fetcher type")
                
                # Process models and calculate RCA scores
                processed_models = []
                for model_data in models:
                    # Map benchmarks to RCA task scores
                    task_scores = self._map_benchmarks_to_rca_tasks(model_data.get('benchmarks', {}))
                    
                    # Calculate RCA score
                    rca_score = self.rca_calculator.calculate_rca_score(task_scores)
                    
                    # Add processed data
                    model_data['task_scores'] = task_scores
                    model_data['rca_score'] = rca_score
                    model_data['id'] = model_data.get('model_id', model_data.get('id', ''))
                    model_data['name'] = model_data.get('model_name', model_data.get('name', ''))
                    processed_models.append(model_data)
                
                print(f"✅ Successfully fetched {len(processed_models)} models from LIVE HuggingFace API")
                # Convert to our data format
                return self._convert_fetched_to_data_format(processed_models)
                
            except Exception as e:
                print(f"❌ Error fetching LIVE data from HuggingFace: {e}")
                raise  # Don't fall back - we want live data only
        
        # Fall back to JSON file only if use_real_data is False
        try:
            with open(self.data_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Data file not found: {self.data_file}")
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON in data file: {self.data_file}")
    
    def _map_benchmarks_to_rca_tasks(self, benchmarks: Dict[str, float]) -> Dict[str, float]:
        """
        Map real benchmark scores to RCA task scores
        Uses the same mapping as benchmark_fetcher for consistency
        """
        BENCHMARK_MAPPING = {
            "code_understanding": {
                "benchmarks": ["humaneval", "mbpp"],
                "weight_distribution": {"humaneval": 0.6, "mbpp": 0.4}
            },
            "log_analysis": {
                "benchmarks": ["arc_challenge"],
                "weight_distribution": {"arc_challenge": 1.0}
            },
            "metric_interpretation": {
                "benchmarks": ["gsm8k"],
                "weight_distribution": {"gsm8k": 1.0}
            },
            "causal_reasoning": {
                "benchmarks": ["hellaswag", "arc_challenge", "winogrande"],
                "weight_distribution": {"hellaswag": 0.4, "arc_challenge": 0.3, "winogrande": 0.3}
            },
            "pattern_recognition": {
                "benchmarks": ["mmlu"],
                "weight_distribution": {"mmlu": 1.0}
            },
            "context_synthesis": {
                "benchmarks": ["mmlu", "truthfulqa"],
                "weight_distribution": {"mmlu": 0.6, "truthfulqa": 0.4}
            },
            "root_cause_identification": {
                "benchmarks": ["arc_challenge", "hellaswag"],
                "weight_distribution": {"arc_challenge": 0.6, "hellaswag": 0.4}
            },
            "solution_recommendation": {
                "benchmarks": ["gsm8k", "arc_challenge"],
                "weight_distribution": {"gsm8k": 0.5, "arc_challenge": 0.5}
            }
        }
        
        rca_scores = {}
        for rca_task, mapping in BENCHMARK_MAPPING.items():
            task_score = 0.0
            total_weight = 0.0
            
            for benchmark, weight in mapping["weight_distribution"].items():
                if benchmark in benchmarks:
                    task_score += benchmarks[benchmark] * weight
                    total_weight += weight
            
            # Normalize if not all benchmarks were available
            if total_weight > 0:
                rca_scores[rca_task] = round(task_score / total_weight, 1)
            else:
                rca_scores[rca_task] = 0.0
        
        return rca_scores
    
    def _convert_fetched_to_data_format(self, models: List[Dict]) -> dict:
        """Convert fetched model data to our internal data format"""
        # Load task definitions from JSON file
        try:
            with open(self.data_file, 'r') as f:
                base_data = json.load(f)
                tasks = base_data.get("tasks", [])
                weights = base_data.get("weights", {})
        except:
            # Use default task definitions
            tasks = [
                {"id": "code_understanding", "name": "Code Understanding",
                 "description": "Ability to parse and comprehend software architecture", "weight": 0.15},
                {"id": "log_analysis", "name": "Log Analysis",
                 "description": "Interpreting error logs and system logs", "weight": 0.20},
                {"id": "metric_interpretation", "name": "Metric Interpretation",
                 "description": "Analyzing time-series data and identifying anomalies", "weight": 0.15},
                {"id": "causal_reasoning", "name": "Causal Reasoning",
                 "description": "Determining cause-effect relationships", "weight": 0.20},
                {"id": "pattern_recognition", "name": "Pattern Recognition",
                 "description": "Identifying recurring issues and patterns", "weight": 0.10},
                {"id": "context_synthesis", "name": "Context Synthesis",
                 "description": "Combining information from multiple sources", "weight": 0.10},
                {"id": "root_cause_identification", "name": "Root Cause Identification",
                 "description": "Pinpointing the underlying cause of issues", "weight": 0.05},
                {"id": "solution_recommendation", "name": "Solution Recommendation",
                 "description": "Suggesting actionable fixes", "weight": 0.05}
            ]
            weights = {task["id"]: task["weight"] for task in tasks}
        
        return {
            "models": models,
            "tasks": tasks,
            "weights": weights
        }
    
    def get_all_models(self) -> List[Model]:
        """
        Get all models (both system and user-submitted)
        
        Returns:
            List of Model objects
        """
        # Get system models and ensure they have source="system"
        system_models = []
        for model_data in self.data.get("models", []):
            # Ensure system models have source="system"
            if "source" not in model_data:
                model_data["source"] = "system"
            system_models.append(Model(**model_data))
        
        # Get user models
        user_models_data = self._load_user_models()
        user_models = [Model(**model) for model in user_models_data]
        
        # Combine and return
        return system_models + user_models
    
    def get_model_by_id(self, model_id: str) -> Optional[Model]:
        """
        Get a specific model by ID
        
        Args:
            model_id: Model identifier
        
        Returns:
            Model object or None if not found
        """
        models = self.get_all_models()
        for model in models:
            if model.id == model_id:
                return model
        return None
    
    def get_task_info(self) -> List[TaskInfo]:
        """
        Get information about all tasks
        
        Returns:
            List of TaskInfo objects
        """
        return [TaskInfo(**task) for task in self.data.get("tasks", [])]
    
    def get_task_leaderboards(self) -> List[TaskLeaderboard]:
        """
        Get leaderboard for each task showing top models
        
        Returns:
            List of TaskLeaderboard objects
        """
        models = self.get_all_models()
        tasks = self.get_task_info()
        leaderboards = []
        
        for task in tasks:
            # Get all model scores for this task
            scores = []
            for model in models:
                task_score = getattr(model.task_scores, task.id)
                scores.append(ModelScore(
                    model=model.id,
                    model_name=model.name,
                    score=task_score
                ))
            
            # Sort by score descending
            scores.sort(key=lambda x: x.score, reverse=True)
            
            # Create leaderboard entry
            leaderboard = TaskLeaderboard(
                id=task.id,
                name=task.name,
                description=task.description,
                weight=task.weight,
                top_model=scores[0].model if scores else "",
                top_score=scores[0].score if scores else 0.0,
                all_scores=scores
            )
            leaderboards.append(leaderboard)
        
        return leaderboards
    
    def get_task_leaderboard_by_id(self, task_id: str) -> Optional[TaskLeaderboard]:
        """
        Get leaderboard for a specific task
        
        Args:
            task_id: Task identifier
        
        Returns:
            TaskLeaderboard object or None if not found
        """
        leaderboards = self.get_task_leaderboards()
        for leaderboard in leaderboards:
            if leaderboard.id == task_id:
                return leaderboard
        return None
    
    def get_models_sorted_by_rca(self, ascending: bool = False) -> List[Model]:
        """
        Get models sorted by RCA score
        
        Args:
            ascending: Sort in ascending order if True, descending if False
        
        Returns:
            List of Model objects sorted by RCA score
        """
        models = self.get_all_models()
        models.sort(key=lambda x: x.rca_score, reverse=not ascending)
        return models
    
    def get_providers(self) -> List[str]:
        """
        Get list of unique model providers
        
        Returns:
            List of provider names
        """
        models = self.get_all_models()
        providers = list(set(model.provider for model in models))
        providers.sort()
        return providers
    
    def filter_models(
        self,
        provider: Optional[str] = None,
        min_rca_score: Optional[float] = None,
        max_rca_score: Optional[float] = None
    ) -> List[Model]:
        """
        Filter models by various criteria
        
        Args:
            provider: Filter by provider name
            min_rca_score: Minimum RCA score
            max_rca_score: Maximum RCA score
        
        Returns:
            List of filtered Model objects
        """
        models = self.get_all_models()
        
        if provider:
            models = [m for m in models if m.provider == provider]
        
        if min_rca_score is not None:
            models = [m for m in models if m.rca_score >= min_rca_score]
        
        if max_rca_score is not None:
            models = [m for m in models if m.rca_score <= max_rca_score]
        
        return models
    
    def _load_user_models(self) -> List[Dict]:
        """Load user-submitted models from JSON file"""
        try:
            with open(self.USER_MODELS_FILE, 'r') as f:
                data = json.load(f)
                return data.get("models", [])
        except FileNotFoundError:
            return []
        except json.JSONDecodeError:
            return []
    
    def _save_user_models(self, models: List[Dict]) -> bool:
        """Save user models to JSON file"""
        try:
            with open(self.USER_MODELS_FILE, 'w') as f:
                json.dump({"models": models}, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving user models: {e}")
            return False
    
    def add_user_model(self, model: Model) -> bool:
        """
        Add a user-submitted model
        
        Args:
            model: Model object to add
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Load existing user models
            user_models = self._load_user_models()
            
            # Check if model already exists
            for existing_model in user_models:
                if existing_model.get("id") == model.id:
                    return False
            
            # Add new model
            user_models.append(model.dict())
            
            # Save to file
            return self._save_user_models(user_models)
        except Exception as e:
            print(f"Error adding user model: {e}")
            return False
    
    def delete_user_model(self, model_id: str) -> bool:
        """
        Delete a user-submitted model
        
        Args:
            model_id: ID of the model to delete
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Load existing user models
            user_models = self._load_user_models()
            
            # Find and remove the model
            initial_count = len(user_models)
            user_models = [m for m in user_models if m.get("id") != model_id]
            
            # Check if anything was removed
            if len(user_models) == initial_count:
                return False  # Model not found
            
            # Save updated list
            return self._save_user_models(user_models)
        except Exception as e:
            print(f"Error deleting user model: {e}")
            return False

        return models

# Made with Bob
