"""
Category Calculator Service
Calculates scores for different leaderboard categories
"""

from typing import Dict, Optional
from abc import ABC, abstractmethod


class CategoryCalculator(ABC):
    """Base class for category-specific score calculators"""
    
    def __init__(self, weights: Optional[Dict[str, float]] = None):
        """
        Initialize calculator with custom or default weights
        
        Args:
            weights: Dictionary of benchmark weights (must sum to 1.0)
        """
        self.weights = weights or self.get_default_weights()
        self._validate_weights()
    
    @abstractmethod
    def get_default_weights(self) -> Dict[str, float]:
        """Return default weights for this category"""
        pass
    
    @abstractmethod
    def get_category_name(self) -> str:
        """Return the category name"""
        pass
    
    @abstractmethod
    def get_category_description(self) -> str:
        """Return the category description"""
        pass
    
    def _validate_weights(self):
        """Validate that weights sum to 1.0"""
        total = sum(self.weights.values())
        if not (0.98 <= total <= 1.02):  # Allow small floating point errors
            raise ValueError(f"Weights must sum to 1.0, got {total}")
    
    def calculate_score(self, benchmarks: Dict[str, float]) -> float:
        """
        Calculate weighted score from benchmark results
        
        Args:
            benchmarks: Dictionary of benchmark scores (0-100)
        
        Returns:
            Category score (0-100), rounded to 1 decimal place
        """
        total_score = 0.0
        total_weight = 0.0
        
        for benchmark, weight in self.weights.items():
            if benchmark in benchmarks and benchmarks[benchmark] is not None:
                total_score += benchmarks[benchmark] * weight
                total_weight += weight
        
        # Normalize if not all benchmarks were available
        if total_weight > 0:
            return round(total_score / total_weight, 1)
        return 0.0
    
    def get_benchmark_weights(self) -> Dict[str, float]:
        """Return the benchmark weights for this category"""
        return self.weights.copy()


class GeneralLLMCalculator(CategoryCalculator):
    """Calculator for General LLM leaderboard (overall performance)"""
    
    def get_default_weights(self) -> Dict[str, float]:
        """
        General LLM weights - balanced across all capabilities
        
        Measures overall language model performance across:
        - Knowledge and understanding
        - Reasoning abilities
        - Mathematical problem solving
        - Code generation
        - Truthfulness
        """
        return {
            # Knowledge (25%)
            "mmlu": 0.25,
            
            # Reasoning (25% total)
            "arc_challenge": 0.10,
            "hellaswag": 0.10,
            "winogrande": 0.05,
            
            # Math (20%)
            "gsm8k": 0.20,
            
            # Coding (20% total)
            "humaneval": 0.11,
            "mbpp": 0.09,
            
            # Truthfulness (10%)
            "truthfulqa": 0.10
        }
    
    def get_category_name(self) -> str:
        return "General LLM"
    
    def get_category_description(self) -> str:
        return "Overall language model performance across knowledge, reasoning, math, coding, and truthfulness"


class CodingCalculator(CategoryCalculator):
    """Calculator for Coding leaderboard"""
    
    def get_default_weights(self) -> Dict[str, float]:
        """
        Coding weights - focused on code generation and understanding
        
        Measures:
        - Code generation from descriptions
        - Code understanding and reasoning
        - Algorithmic problem solving
        """
        return {
            # Code Generation (40% total)
            "humaneval": 0.25,  # Primary code generation benchmark
            "mbpp": 0.15,       # Python code generation
            
            # Code Reasoning (30%)
            "arc_challenge": 0.30,  # Logical reasoning (proxy for code understanding)
            
            # Problem Solving (30%)
            "gsm8k": 0.30  # Math/algorithmic thinking
        }
    
    def get_category_name(self) -> str:
        return "Coding"
    
    def get_category_description(self) -> str:
        return "Code generation, understanding, and algorithmic problem-solving abilities"


class ReasoningCalculator(CategoryCalculator):
    """Calculator for Reasoning leaderboard"""
    
    def get_default_weights(self) -> Dict[str, float]:
        """
        Reasoning weights - focused on logical and analytical thinking
        
        Measures:
        - Logical reasoning
        - Commonsense reasoning
        - Mathematical reasoning
        - Causal reasoning
        """
        return {
            # Logical Reasoning (30%)
            "arc_challenge": 0.30,
            
            # Commonsense Reasoning (30% total)
            "hellaswag": 0.20,
            "winogrande": 0.10,
            
            # Mathematical Reasoning (25%)
            "gsm8k": 0.25,
            
            # Knowledge-based Reasoning (15%)
            "mmlu": 0.15
        }
    
    def get_category_name(self) -> str:
        return "Reasoning"
    
    def get_category_description(self) -> str:
        return "Logical, commonsense, and mathematical reasoning capabilities"


class RCACalculator(CategoryCalculator):
    """Calculator for RCA (Root Cause Analysis) leaderboard"""
    
    def get_default_weights(self) -> Dict[str, float]:
        """
        RCA weights - focused on root cause analysis tasks
        
        This uses a task-based approach where benchmarks are mapped to RCA tasks
        """
        # This is a simplified version - the actual RCA calculator
        # uses task-based scoring (see rca_calculator.py)
        return {
            "humaneval": 0.09,      # Code understanding (15% * 0.6)
            "mbpp": 0.06,           # Code understanding (15% * 0.4)
            "arc_challenge": 0.31,  # Multiple tasks
            "gsm8k": 0.175,         # Metric interpretation + solution
            "hellaswag": 0.12,      # Causal reasoning + root cause ID
            "winogrande": 0.06,     # Causal reasoning
            "mmlu": 0.165,          # Pattern recognition + context synthesis
            "truthfulqa": 0.04      # Context synthesis
        }
    
    def get_category_name(self) -> str:
        return "RCA"
    
    def get_category_description(self) -> str:
        return "Root Cause Analysis capabilities across code understanding, log analysis, and causal reasoning"


# Category registry
CATEGORY_CALCULATORS = {
    "general": GeneralLLMCalculator,
    "coding": CodingCalculator,
    "reasoning": ReasoningCalculator,
    "rca": RCACalculator
}


def get_calculator(category: str) -> CategoryCalculator:
    """
    Get calculator instance for a category
    
    Args:
        category: Category name (general, coding, reasoning, rca)
    
    Returns:
        CategoryCalculator instance
    
    Raises:
        ValueError: If category is not recognized
    """
    if category not in CATEGORY_CALCULATORS:
        raise ValueError(f"Unknown category: {category}. Available: {list(CATEGORY_CALCULATORS.keys())}")
    
    return CATEGORY_CALCULATORS[category]()


def get_all_categories() -> Dict[str, Dict[str, str]]:
    """
    Get information about all available categories
    
    Returns:
        Dictionary with category info (name, description, icon)
    """
    categories = {}
    icons = {
        "rca": "🔍",
        "general": "🤖",
        "coding": "💻",
        "reasoning": "🧠"
    }
    
    for category_id, calculator_class in CATEGORY_CALCULATORS.items():
        calc = calculator_class()
        categories[category_id] = {
            "id": category_id,
            "name": calc.get_category_name(),
            "description": calc.get_category_description(),
            "icon": icons.get(category_id, "📊")
        }
    
    return categories

# Made with Bob
