"""
RCA Score Calculator Service
Calculates the RCA suitability score based on weighted task performance
"""

from typing import Dict, Optional


class RCACalculator:
    """Calculate RCA suitability scores for LLM models"""
    
    # Default weights for RCA tasks
    DEFAULT_WEIGHTS = {
        "code_understanding": 0.15,
        "log_analysis": 0.20,
        "metric_interpretation": 0.15,
        "causal_reasoning": 0.20,
        "pattern_recognition": 0.10,
        "context_synthesis": 0.10,
        "root_cause_identification": 0.05,
        "solution_recommendation": 0.05
    }
    
    def __init__(self, weights: Optional[Dict[str, float]] = None):
        """
        Initialize the RCA calculator with custom or default weights
        
        Args:
            weights: Dictionary of task weights (must sum to 1.0)
        """
        self.weights = weights or self.DEFAULT_WEIGHTS
        self._validate_weights()
    
    def _validate_weights(self):
        """Validate that weights sum to 1.0"""
        total = sum(self.weights.values())
        if not (0.99 <= total <= 1.01):  # Allow small floating point errors
            raise ValueError(f"Weights must sum to 1.0, got {total}")
    
    def calculate_rca_score(self, task_scores: Dict[str, float]) -> float:
        """
        Calculate weighted RCA score from individual task scores
        
        Formula: RCA Score = Σ(task_score × task_weight)
        
        Args:
            task_scores: Dictionary of task scores (0-100)
        
        Returns:
            RCA score (0-100), rounded to 1 decimal place
        """
        rca_score = 0.0
        
        for task, score in task_scores.items():
            weight = self.weights.get(task, 0)
            rca_score += score * weight
        
        return round(rca_score, 1)
    
    def get_rating_category(self, rca_score: float) -> str:
        """
        Get the rating category for an RCA score
        
        Args:
            rca_score: RCA score (0-100)
        
        Returns:
            Rating category string
        """
        if rca_score >= 90:
            return "Excellent for RCA"
        elif rca_score >= 80:
            return "Very Good for RCA"
        elif rca_score >= 70:
            return "Good for RCA"
        elif rca_score >= 60:
            return "Fair for RCA"
        else:
            return "Not Recommended for RCA"
    
    def get_rating_color(self, rca_score: float) -> str:
        """
        Get the color code for an RCA score
        
        Args:
            rca_score: RCA score (0-100)
        
        Returns:
            Color name string
        """
        if rca_score >= 90:
            return "green"
        elif rca_score >= 80:
            return "yellow-green"
        elif rca_score >= 70:
            return "yellow"
        elif rca_score >= 60:
            return "orange"
        else:
            return "red"
    
    def get_task_contribution(self, task_scores: Dict[str, float]) -> Dict[str, float]:
        """
        Calculate each task's contribution to the overall RCA score
        
        Args:
            task_scores: Dictionary of task scores (0-100)
        
        Returns:
            Dictionary of task contributions (weighted scores)
        """
        contributions = {}
        
        for task, score in task_scores.items():
            weight = self.weights.get(task, 0)
            contributions[task] = round(score * weight, 2)
        
        return contributions

# Made with Bob
