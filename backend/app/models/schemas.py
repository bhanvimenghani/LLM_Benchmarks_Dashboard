from pydantic import BaseModel, Field, validator
from typing import Dict, Optional
from datetime import datetime


class TaskScore(BaseModel):
    code_understanding: float = Field(..., ge=0, le=100, description="Score between 0-100")
    log_analysis: float = Field(..., ge=0, le=100, description="Score between 0-100")
    metric_interpretation: float = Field(..., ge=0, le=100, description="Score between 0-100")
    causal_reasoning: float = Field(..., ge=0, le=100, description="Score between 0-100")
    pattern_recognition: float = Field(..., ge=0, le=100, description="Score between 0-100")
    context_synthesis: float = Field(..., ge=0, le=100, description="Score between 0-100")
    root_cause_identification: float = Field(..., ge=0, le=100, description="Score between 0-100")
    solution_recommendation: float = Field(..., ge=0, le=100, description="Score between 0-100")


class ModelMetadata(BaseModel):
    parameters: str
    context_window: int = Field(..., gt=0, description="Context window size")
    release_date: str


class Model(BaseModel):
    id: str
    name: str
    provider: str
    version: str
    task_scores: TaskScore
    rca_score: float
    metadata: ModelMetadata
    source: Optional[str] = "user"  # "user" or "huggingface"
    last_updated: Optional[str] = None


class UserModelInput(BaseModel):
    """Schema for user-submitted models"""
    name: str = Field(..., min_length=1, max_length=100, description="Model name")
    provider: str = Field(..., min_length=1, max_length=50, description="Provider name")
    version: str = Field(..., min_length=1, max_length=50, description="Model version")
    task_scores: TaskScore
    metadata: ModelMetadata
    
    @validator('name', 'provider', 'version')
    def validate_no_special_chars(cls, v):
        """Ensure no special characters that could cause issues"""
        if not v.replace('-', '').replace('_', '').replace('.', '').replace(' ', '').isalnum():
            raise ValueError('Only alphanumeric characters, hyphens, underscores, dots, and spaces allowed')
        return v


class UserModelResponse(BaseModel):
    """Response after adding a user model"""
    success: bool
    message: str
    model: Optional[Model] = None


class HuggingFaceModelInput(BaseModel):
    """Schema for fetching model from HuggingFace"""
    huggingface_url: str = Field(..., min_length=1, description="HuggingFace model URL or ID")


class HuggingFaceModelResponse(BaseModel):
    """Response after fetching from HuggingFace"""
    success: bool
    message: str
    model_info: Optional[Dict] = None
    benchmarks: Optional[Dict[str, float]] = None
    task_scores: Optional[Dict[str, float]] = None
    rca_score: Optional[float] = None
    assessment: Optional[str] = None
    # Fields for model rejection
    suitable_for_rca: Optional[bool] = None
    model_type: Optional[str] = None
    pipeline_tag: Optional[str] = None
    rejection_reason: Optional[str] = None


class TaskInfo(BaseModel):
    id: str
    name: str
    description: str
    weight: float


class ModelScore(BaseModel):
    model: str
    model_name: str
    score: float


class TaskLeaderboard(BaseModel):
    id: str
    name: str
    description: str
    weight: float
    top_model: str
    top_score: float
    all_scores: list[ModelScore]


class LeaderboardEntry(BaseModel):
    rank: int
    model: Model
    rca_score: float


class ModelsResponse(BaseModel):
    models: list[Model]
    count: int


class TasksResponse(BaseModel):
    tasks: list[TaskLeaderboard]


class LeaderboardResponse(BaseModel):
    leaderboard: list[LeaderboardEntry]

# Made with Bob
