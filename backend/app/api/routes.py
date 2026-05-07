"""
API Routes
Defines all API endpoints for the RCA Benchmarking Dashboard
"""

from fastapi import APIRouter, HTTPException
from typing import Optional
from datetime import datetime
from ..models.schemas import (
    ModelsResponse,
    TasksResponse,
    LeaderboardResponse,
    LeaderboardEntry,
    Model,
    UserModelInput,
    UserModelResponse,
    HuggingFaceModelInput,
    HuggingFaceModelResponse,
    TaskScore,
    ModelMetadata
)
from ..services.data_service import DataService
from ..services.rca_calculator import RCACalculator
from ..services.huggingface_service import HuggingFaceService
from ..services.category_calculator import get_calculator, get_all_categories

router = APIRouter()
data_service = DataService()
rca_calculator = RCACalculator()
hf_service = HuggingFaceService()


@router.get("/models", response_model=ModelsResponse)
async def get_models(
    provider: Optional[str] = None,
    min_rca_score: Optional[float] = None,
    max_rca_score: Optional[float] = None
):
    """
    Get all models with optional filtering
    
    Query Parameters:
        - provider: Filter by provider name
        - min_rca_score: Minimum RCA score
        - max_rca_score: Maximum RCA score
    """
    try:
        if provider or min_rca_score or max_rca_score:
            models = data_service.filter_models(
                provider=provider,
                min_rca_score=min_rca_score,
                max_rca_score=max_rca_score
            )
        else:
            models = data_service.get_all_models()
        
        return ModelsResponse(models=models, count=len(models))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models/{model_id}", response_model=Model)
async def get_model(model_id: str):
    """
    Get detailed information for a specific model
    
    Path Parameters:
        - model_id: Model identifier
    """
    try:
        model = data_service.get_model_by_id(model_id)
        if not model:
            raise HTTPException(status_code=404, detail=f"Model '{model_id}' not found")
        return model
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks", response_model=TasksResponse)
async def get_tasks():
    """
    Get all tasks with leaderboard showing top models for each task
    """
    try:
        tasks = data_service.get_task_leaderboards()
        return TasksResponse(tasks=tasks)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks/{task_id}")
async def get_task_leaderboard(task_id: str):
    """
    Get leaderboard for a specific task
    
    Path Parameters:
        - task_id: Task identifier
    """
    try:
        task = data_service.get_task_leaderboard_by_id(task_id)
        if not task:
            raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found")
        return task
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/leaderboard", response_model=LeaderboardResponse)
async def get_leaderboard(ascending: bool = False):
    """
    Get overall RCA leaderboard with models ranked by RCA score
    
    Query Parameters:
        - ascending: Sort in ascending order if true, descending if false (default)
    """
    try:
        models = data_service.get_models_sorted_by_rca(ascending=ascending)
        
        leaderboard = [
            LeaderboardEntry(
                rank=idx + 1,
                model=model,
                rca_score=model.rca_score
            )
            for idx, model in enumerate(models)
        ]
        
        return LeaderboardResponse(leaderboard=leaderboard)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/providers")
async def get_providers():
    """
    Get list of all model providers
    """
    try:
        providers = data_service.get_providers()
        return {"providers": providers}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {
        "status": "healthy",
        "service": "RCA Benchmarking API",
        "version": "1.0.0"
    }


@router.post("/models", response_model=UserModelResponse)
async def add_user_model(model_input: UserModelInput):
    """
    Add a custom user model to the dashboard
    
    Request Body:
        - UserModelInput: Model details including name, provider, version, task scores, and metadata
    """
    try:
        # Generate model ID from name
        model_id = model_input.name.lower().replace(' ', '-').replace('_', '-')
        
        # Check if model already exists
        existing_model = data_service.get_model_by_id(model_id)
        if existing_model:
            raise HTTPException(
                status_code=409, 
                detail=f"Model with ID '{model_id}' already exists. Please use a different name."
            )
        
        # Calculate RCA score
        task_scores_dict = model_input.task_scores.dict()
        rca_score = rca_calculator.calculate_rca_score(task_scores_dict)
        
        # Create model object
        new_model = Model(
            id=model_id,
            name=model_input.name,
            provider=model_input.provider,
            version=model_input.version,
            task_scores=model_input.task_scores,
            rca_score=rca_score,
            metadata=model_input.metadata,
            source="user",
            last_updated=datetime.now().isoformat()
        )
        
        # Save to user models file
        success = data_service.add_user_model(new_model)
        
        if success:
            return UserModelResponse(
                success=True,
                message=f"Model '{model_input.name}' added successfully with RCA score {rca_score:.1f}",
                model=new_model
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to save model")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding model: {str(e)}")


@router.delete("/models/{model_id}")
async def delete_user_model(model_id: str):
    """
    Delete a user-submitted model
    
    Path Parameters:
        - model_id: Model identifier
    """
    try:
        success = data_service.delete_user_model(model_id)
        
        if success:
            return {"success": True, "message": f"Model '{model_id}' deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail=f"Model '{model_id}' not found or cannot be deleted")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting model: {str(e)}")


@router.post("/models/fetch-from-huggingface", response_model=HuggingFaceModelResponse)
async def fetch_from_huggingface(input_data: HuggingFaceModelInput):
    """
    Fetch model information from HuggingFace and calculate RCA scores
    
    Request Body:
        - huggingface_url: HuggingFace model URL or ID
    
    Returns:
        - Model information with calculated RCA scores based on benchmarks
        - Or rejection message if model is not suitable for RCA
    """
    try:
        # Process HuggingFace model
        result = hf_service.process_huggingface_model(input_data.huggingface_url)
        
        # Check if model was rejected
        if result.get('suitable_for_rca') == False:
            return HuggingFaceModelResponse(
                success=False,
                message=result.get('message', 'Model not suitable for RCA'),
                rejection_reason=result.get('rejection_reason'),
                suitable_for_rca=False,
                model_type=result.get('model_type'),
                pipeline_tag=result.get('pipeline_tag')
            )
        
        # Model is suitable, return full data
        return HuggingFaceModelResponse(
            success=True,
            message=f"Successfully fetched model data. Found {result['benchmarks_found']} benchmarks.",
            model_info={
                "name": result["name"],
                "provider": result["provider"],
                "version": result.get("version", "latest"),
                "parameters": result.get("parameters", "Unknown"),
                "context_window": result.get("context_window", 8192)
            },
            benchmarks=result.get("benchmarks", {}),
            task_scores=result.get("task_scores", {}),
            rca_score=result.get("rca_score", 0),
            assessment=result.get("assessment", ""),
            suitable_for_rca=True
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching from HuggingFace: {str(e)}")


@router.post("/models/add-from-huggingface", response_model=UserModelResponse)
async def add_from_huggingface(input_data: HuggingFaceModelInput):
    """
    Fetch model from HuggingFace and add it to the dashboard
    
    Request Body:
        - huggingface_url: HuggingFace model URL or ID
    """
    try:
        # Process HuggingFace model
        result = hf_service.process_huggingface_model(input_data.huggingface_url)
        
        # Generate model ID
        model_id = result["name"].lower().replace(' ', '-').replace('_', '-')
        
        # Check if model already exists
        existing_model = data_service.get_model_by_id(model_id)
        if existing_model:
            raise HTTPException(
                status_code=409,
                detail=f"Model with ID '{model_id}' already exists. Please use a different name."
            )
        
        # Create TaskScore object
        task_scores = TaskScore(**result["task_scores"])
        
        # Create ModelMetadata object
        metadata = ModelMetadata(
            parameters=result["parameters"],
            context_window=result["context_window"],
            release_date=datetime.now().strftime("%Y-%m-%d")
        )
        
        # Create Model object
        new_model = Model(
            id=model_id,
            name=result["name"],
            provider=result["provider"],
            version=result["version"],
            task_scores=task_scores,
            rca_score=result["rca_score"],
            metadata=metadata,
            source="huggingface",
            last_updated=datetime.now().isoformat()
        )
        
        # Save to user models file
        success = data_service.add_user_model(new_model)
        
        if success:
            return UserModelResponse(
                success=True,
                message=f"Model '{result['name']}' added successfully from HuggingFace with RCA score {result['rca_score']:.1f}. {result['assessment']}.",
                model=new_model
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to save model")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding model from HuggingFace: {str(e)}")


@router.get("/categories")
async def get_categories():
    """
    Get all available leaderboard categories
    
    Returns:
        Dictionary of categories with their metadata (name, description, icon)
    """
    try:
        categories = get_all_categories()
        return {"categories": categories}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/leaderboard/{category}")
async def get_category_leaderboard(category: str, ascending: bool = False, limit: Optional[int] = None):
    """
    Get leaderboard for a specific category
    
    Path Parameters:
        - category: Category ID (rca, general, coding, reasoning)
    
    Query Parameters:
        - ascending: Sort in ascending order if true, descending if false (default)
        - limit: Maximum number of models to return (default: 6 for RCA, unlimited for others)
    
    Returns:
        Leaderboard with models ranked by category-specific score
    """
    try:
        # Get the calculator for this category
        calculator = get_calculator(category)
        
        # Get models from data service (uses live data)
        all_models = data_service.get_all_models()
        
        # Calculate category scores for each model
        models_with_scores = []
        for model in all_models:
            # Get benchmark scores from model data
            benchmarks = {}
            
            # Try to get benchmarks from metadata first
            if hasattr(model, 'metadata') and model.metadata:
                if hasattr(model.metadata, 'benchmarks') and model.metadata.benchmarks:
                    benchmarks = model.metadata.benchmarks
                elif isinstance(model.metadata, dict) and 'benchmarks' in model.metadata:
                    benchmarks = model.metadata['benchmarks']
            
            # Skip models without benchmark data
            if not benchmarks:
                continue
            
            # Calculate category score
            category_score = calculator.calculate_score(benchmarks)
            
            models_with_scores.append({
                'id': model.id,
                'name': model.name,
                'provider': model.provider,
                'version': model.version if hasattr(model, 'version') else 'latest',
                'category_score': category_score,
                'rca_score': model.rca_score,
                'metadata': model.metadata.dict() if hasattr(model.metadata, 'dict') else (model.metadata if model.metadata else {}),
                'benchmarks': benchmarks
            })
        
        # Sort by category score
        models_with_scores.sort(
            key=lambda x: x['category_score'],
            reverse=not ascending
        )
        
        # Apply default limit of 6 for all categories
        if limit is None:
            limit = 6
        
        # Apply limit
        models_with_scores = models_with_scores[:limit]
        
        # Create leaderboard entries
        leaderboard = [
            {
                'rank': idx + 1,
                'model': {
                    'id': entry['id'],
                    'name': entry['name'],
                    'provider': entry['provider'],
                    'version': entry['version'],
                    'metadata': entry['metadata']
                },
                'score': entry['category_score'],
                'rca_score': entry['rca_score'],
                'key_benchmarks': {
                    k: v for k, v in entry['benchmarks'].items()
                    if k in ['humaneval', 'mmlu', 'gsm8k', 'arc_challenge']
                }
            }
            for idx, entry in enumerate(models_with_scores)
        ]
        
        return {
            'category': category,
            'category_name': calculator.get_category_name(),
            'category_description': calculator.get_category_description(),
            'leaderboard': leaderboard,
            'count': len(leaderboard),
            'total_models': len(models_with_scores) if limit is None else len(leaderboard)
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching category leaderboard: {str(e)}")


@router.get("/categories/{category}/info")
async def get_category_info(category: str):
    """
    Get detailed information about a category
    
    Path Parameters:
        - category: Category ID (rca, general, coding, reasoning)
    
    Returns:
        Category metadata including benchmark weights and descriptions
    """
    try:
        calculator = get_calculator(category)
        
        return {
            'id': category,
            'name': calculator.get_category_name(),
            'description': calculator.get_category_description(),
            'weights': calculator.get_benchmark_weights()
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/refresh/status")
async def get_refresh_status():
    """
    Get the status of the auto-refresh service
    
    Returns:
        Current refresh status including last update time and next scheduled refresh
    """
    try:
        from ..services.auto_refresh import get_auto_refresh_service
        service = get_auto_refresh_service()
        return service.get_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/refresh/force")
async def force_refresh():
    """
    Force an immediate data refresh from all sources
    
    Returns:
        Refresh status after completion
    """
    try:
        from ..services.auto_refresh import get_auto_refresh_service
        service = get_auto_refresh_service()
        await service.force_refresh()
        return {
            'success': True,
            'message': 'Data refresh completed',
            'status': service.get_status()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Refresh failed: {str(e)}")


@router.get("/data-sources")
async def get_data_sources():
    """
    Get information about data sources (Vellum-style transparency)
    
    Returns:
        List of data sources with their status and reliability
    """
    return {
        'sources': [
            {
                'name': 'HuggingFace Open LLM Leaderboard',
                'type': 'public_benchmark',
                'reliability': 'high',
                'status': 'active',
                'description': 'Industry-standard benchmarks from HuggingFace',
                'benchmarks': ['MMLU', 'ARC', 'HellaSwag', 'GSM8K', 'HumanEval', 'TruthfulQA']
            },
            {
                'name': 'LMSYS Chatbot Arena',
                'type': 'community_evaluation',
                'reliability': 'high',
                'status': 'planned',
                'description': 'Human preference ratings and Elo scores',
                'benchmarks': ['Elo Rating', 'Human Preference']
            },
            {
                'name': 'Provider APIs',
                'type': 'direct_integration',
                'reliability': 'high',
                'status': 'planned',
                'description': 'Direct integration with OpenAI, Anthropic, Google',
                'benchmarks': ['Model Metadata', 'Version Info']
            },
            {
                'name': 'Technical Reports',
                'type': 'manual_curation',
                'reliability': 'medium',
                'status': 'active',
                'description': 'Official model cards and research papers',
                'benchmarks': ['All Benchmarks']
            }
        ],
        'aggregation_method': 'weighted_average',
        'confidence_scoring': True,
        'multi_source_validation': True
    }


@router.get("/model/{model_id}/sources")
async def get_model_sources(model_id: str):
    """
    Get data sources for a specific model (transparency feature)
    
    Path Parameters:
        - model_id: Model identifier
    
    Returns:
        List of sources that provided data for this model with confidence scores
    """
    try:
        # Get model from data service
        model = data_service.get_model_by_id(model_id)
        
        if not model:
            raise HTTPException(status_code=404, detail=f"Model {model_id} not found")
        
        # Extract benchmarks from model metadata
        benchmarks = {}
        if hasattr(model, 'metadata') and model.metadata:
            if isinstance(model.metadata, dict) and 'benchmarks' in model.metadata:
                benchmarks = model.metadata['benchmarks']
            elif hasattr(model.metadata, 'dict'):
                metadata_dict = model.metadata.dict()
                benchmarks = metadata_dict.get('benchmarks', {})
        
        # Determine source
        source = getattr(model, 'source', 'huggingface')
        
        return {
            'model_id': model_id,
            'model_name': model.name,
            'sources': [source],
            'confidence_score': 85.0 if source in ['huggingface', 'lmsys'] else 75.0,
            'last_updated': getattr(model, 'last_updated', datetime.now().isoformat()),
            'benchmarks': {
                name: {
                    'value': value,
                    'source': source
                }
                for name, value in benchmarks.items()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Made with Bob
