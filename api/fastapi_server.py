"""
FastAPI REST API Server for Photo Analysis Agents

Exposes the travel photo analysis agents as RESTful API endpoints.

Usage:
    uvicorn api.fastapi_server:app --host 0.0.0.0 --port 8000 --reload

API Documentation:
    http://localhost:8000/docs (Swagger UI)
    http://localhost:8000/redoc (ReDoc)
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Depends, Header
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from pathlib import Path
from datetime import datetime
import uuid
import logging
import yaml
import shutil
import tempfile
import asyncio
import os
from concurrent.futures import ThreadPoolExecutor

# Import agents
import sys
sys.path.append(str(Path(__file__).parent.parent))

from agents.aesthetic_assessment import AestheticAssessmentAgent
from agents.filtering_categorization import FilteringCategorizationAgent
from agents.caption_generation import CaptionGenerationAgent
from agents.metadata_extraction import MetadataExtractionAgent
from agents.quality_assessment import QualityAssessmentAgent
from utils.logger import setup_logger

# Initialize FastAPI app
app = FastAPI(
    title="Travel Photo Analysis API",
    description="AI-powered travel photo analysis with aesthetic scoring, categorization, and caption generation",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
job_storage: Dict[str, Dict[str, Any]] = {}
executor = ThreadPoolExecutor(max_workers=4)

# Load configuration
config_path = Path(__file__).parent.parent / "config.yaml"
with open(config_path, 'r') as f:
    config = yaml.safe_load(f)

# Setup Google Cloud authentication from keys.json
keys_path = Path(__file__).parent.parent / "keys.json"
if keys_path.exists():
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(keys_path)
    logger_temp = logging.getLogger("API_SETUP")
    logger_temp.info(f"Using Google Cloud credentials from: {keys_path}")
else:
    logger_temp = logging.getLogger("API_SETUP")
    logger_temp.warning("keys.json not found - using default credentials")

# Setup logger
log_level = config.get('logging', {}).get('level', 'INFO')
logger = setup_logger("API", log_level)

# Initialize agents (lazy loading)
agents_cache = {}


def get_agents():
    """Get or initialize agents (singleton pattern)"""
    if not agents_cache:
        agents_cache['metadata'] = MetadataExtractionAgent(config, logger)
        agents_cache['quality'] = QualityAssessmentAgent(config, logger)
        agents_cache['aesthetic'] = AestheticAssessmentAgent(config, logger)
        agents_cache['filtering'] = FilteringCategorizationAgent(config, logger)
        agents_cache['caption'] = CaptionGenerationAgent(config, logger)
        logger.info("Agents initialized successfully")
    return agents_cache


# Pydantic models for request/response

class AnalysisRequest(BaseModel):
    """Request model for photo analysis"""
    agents: List[str] = Field(
        default=["aesthetic", "filtering", "caption"],
        description="List of agents to run: metadata, quality, aesthetic, filtering, caption"
    )
    include_token_usage: bool = Field(
        default=True,
        description="Include token usage and cost information in response"
    )


class AestheticScores(BaseModel):
    """Aesthetic assessment scores"""
    composition: int = Field(..., ge=1, le=5)
    framing: int = Field(..., ge=1, le=5)
    lighting: int = Field(..., ge=1, le=5)
    subject_interest: int = Field(..., ge=1, le=5)
    overall_aesthetic: int = Field(..., ge=1, le=5)
    notes: str


class FilteringResult(BaseModel):
    """Filtering and categorization result"""
    category: str
    subcategories: List[str]
    time_category: str
    location: Optional[str]
    passes_filter: bool
    flagged: bool
    flags: List[str]
    reasoning: str


class CaptionResult(BaseModel):
    """Caption generation result"""
    concise: str
    standard: str
    detailed: str
    keywords: List[str] = Field(default_factory=list)


class TokenUsage(BaseModel):
    """Token usage and cost information"""
    prompt_token_count: int
    candidates_token_count: int
    total_token_count: int
    estimated_cost_usd: float


class AnalysisResponse(BaseModel):
    """Complete analysis response"""
    job_id: str
    status: str
    image_id: str
    metadata: Optional[Dict[str, Any]] = None
    quality: Optional[Dict[str, Any]] = None
    aesthetic: Optional[AestheticScores] = None
    filtering: Optional[FilteringResult] = None
    caption: Optional[CaptionResult] = None
    token_usage: Optional[Dict[str, TokenUsage]] = None
    total_cost_usd: Optional[float] = None
    processing_time_seconds: Optional[float] = None


class JobStatus(BaseModel):
    """Job status response"""
    job_id: str
    status: str  # pending, processing, completed, failed
    progress: int  # 0-100
    message: Optional[str] = None
    result: Optional[AnalysisResponse] = None


class TokenUsageStats(BaseModel):
    """Aggregate token usage statistics"""
    total_requests: int
    total_tokens: int
    total_cost_usd: float
    by_agent: Dict[str, Dict[str, Any]]


# Authentication (simple API key for demo)
API_KEY = os.getenv("API_KEY", "your-secret-api-key-here")


async def verify_api_key(x_api_key: str = Header(None)):
    """Verify API key from header"""
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key


# API Endpoints

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "Travel Photo Analysis API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check if agents can be initialized
        get_agents()
        return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "error": str(e)}
        )


@app.post("/api/v1/analyze/image", response_model=AnalysisResponse)
async def analyze_image(
    file: UploadFile = File(...),
    request: AnalysisRequest = Depends(),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    api_key: str = Depends(verify_api_key)
):
    """
    Analyze a single image with specified agents.

    **Supported agents**: metadata, quality, aesthetic, filtering, caption

    **Returns**: Complete analysis results with token usage
    """
    job_id = str(uuid.uuid4())
    start_time = datetime.utcnow()

    # Save uploaded file temporarily
    temp_dir = tempfile.mkdtemp()
    temp_path = Path(temp_dir) / file.filename

    try:
        with open(temp_path, 'wb') as buffer:
            shutil.copyfileobj(file.file, buffer)

        logger.info(f"Processing image: {file.filename} (job: {job_id})")

        # Run analysis
        result = await run_analysis(temp_path, request.agents, request.include_token_usage)

        # Calculate processing time
        processing_time = (datetime.utcnow() - start_time).total_seconds()

        # Build response
        response = AnalysisResponse(
            job_id=job_id,
            status="completed",
            image_id=temp_path.stem,
            metadata=result.get('metadata'),
            quality=result.get('quality'),
            aesthetic=result.get('aesthetic'),
            filtering=result.get('filtering'),
            caption=result.get('caption'),
            token_usage=result.get('token_usage') if request.include_token_usage else None,
            total_cost_usd=result.get('total_cost_usd'),
            processing_time_seconds=processing_time
        )

        # Clean up in background
        background_tasks.add_task(cleanup_temp_dir, temp_dir)

        return response

    except Exception as e:
        logger.error(f"Analysis failed for {file.filename}: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.post("/api/v1/analyze/batch")
async def analyze_batch(
    files: List[UploadFile] = File(...),
    agents: List[str] = ["aesthetic", "filtering", "caption"],
    api_key: str = Depends(verify_api_key)
):
    """
    Submit batch analysis job (async processing).

    **Returns**: Job ID for status checking
    """
    job_id = str(uuid.uuid4())

    # Create job record
    job_storage[job_id] = {
        "status": "pending",
        "progress": 0,
        "total_images": len(files),
        "processed_images": 0,
        "created_at": datetime.utcnow().isoformat(),
        "results": []
    }

    # TODO: Process in background task or queue
    # For now, return job ID

    return {
        "job_id": job_id,
        "status": "pending",
        "total_images": len(files),
        "message": "Batch job submitted. Use GET /api/v1/analyze/status/{job_id} to check progress"
    }


@app.get("/api/v1/analyze/status/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str, api_key: str = Depends(verify_api_key)):
    """Get status of batch analysis job"""
    if job_id not in job_storage:
        raise HTTPException(status_code=404, detail="Job not found")

    job = job_storage[job_id]

    return JobStatus(
        job_id=job_id,
        status=job["status"],
        progress=job["progress"],
        message=job.get("message"),
        result=job.get("result")
    )


@app.post("/api/v1/agents/aesthetic")
async def run_aesthetic_only(
    file: UploadFile = File(...),
    api_key: str = Depends(verify_api_key)
):
    """Run aesthetic assessment agent only"""
    return await analyze_image(file, AnalysisRequest(agents=["aesthetic"]), BackgroundTasks(), api_key)


@app.post("/api/v1/agents/filtering")
async def run_filtering_only(
    file: UploadFile = File(...),
    api_key: str = Depends(verify_api_key)
):
    """Run filtering & categorization agent only"""
    return await analyze_image(file, AnalysisRequest(agents=["filtering"]), BackgroundTasks(), api_key)


@app.post("/api/v1/agents/caption")
async def run_caption_only(
    file: UploadFile = File(...),
    api_key: str = Depends(verify_api_key)
):
    """Run caption generation agent only"""
    return await analyze_image(file, AnalysisRequest(agents=["caption"]), BackgroundTasks(), api_key)


@app.get("/api/v1/usage/tokens", response_model=TokenUsageStats)
async def get_token_usage(api_key: str = Depends(verify_api_key)):
    """Get aggregate token usage statistics"""
    # TODO: Implement persistent storage for usage tracking
    return TokenUsageStats(
        total_requests=0,
        total_tokens=0,
        total_cost_usd=0.0,
        by_agent={}
    )


# Helper functions

async def run_analysis(
    image_path: Path,
    requested_agents: List[str],
    include_token_usage: bool
) -> Dict[str, Any]:
    """Run requested agents on image"""
    logger.info(f"run_analysis called with agents: {requested_agents}")
    agents = get_agents()
    result = {}
    total_cost = 0.0

    # Always run metadata first
    metadata_list, _ = agents['metadata'].run([image_path])
    metadata = metadata_list[0] if metadata_list else {}
    logger.info(f"Metadata extracted: {metadata.get('image_id')}")
    
    # Always include metadata in response
    result['metadata'] = metadata

    # Run quality if needed for filtering (or if requested)
    if 'quality' in requested_agents or 'filtering' in requested_agents or 'caption' in requested_agents:
        quality_list, _ = agents['quality'].run([image_path], [metadata])
        quality = quality_list[0] if quality_list else {}
        result['quality'] = quality
    else:
        quality = {}

    # Run aesthetic
    if 'aesthetic' in requested_agents:
        logger.info("Running aesthetic agent...")
        aesthetic_list, validation = agents['aesthetic'].run([image_path], [metadata])
        aesthetic = aesthetic_list[0] if aesthetic_list else {}
        logger.info(f"Aesthetic result: {aesthetic.get('overall_aesthetic')}")
        result['aesthetic'] = aesthetic

        if include_token_usage and 'token_usage' in aesthetic:
            result.setdefault('token_usage', {})['aesthetic'] = aesthetic['token_usage']
            total_cost += aesthetic['token_usage'].get('estimated_cost_usd', 0)
    else:
        aesthetic = {}

    # Run filtering
    if 'filtering' in requested_agents:
        filtering_list, validation = agents['filtering'].run(
            [image_path], [metadata], [quality], [aesthetic] if aesthetic else [{}]
        )
        filtering = filtering_list[0] if filtering_list else {}
        result['filtering'] = filtering

        if include_token_usage and 'token_usage' in filtering:
            result.setdefault('token_usage', {})['filtering'] = filtering['token_usage']
            total_cost += filtering['token_usage'].get('estimated_cost_usd', 0)
    else:
        filtering = {}

    # Run caption
    if 'caption' in requested_agents:
        caption_list, validation = agents['caption'].run(
            [image_path], [metadata], [quality], [aesthetic] if aesthetic else [{}], [filtering] if filtering else [{}]
        )
        caption = caption_list[0] if caption_list else {}
        # Include both captions and keywords in the response
        caption_response = caption.get('captions', {}) if 'captions' in caption else caption
        if isinstance(caption_response, dict):
            caption_response['keywords'] = caption.get('keywords', [])
        result['caption'] = caption_response

        if include_token_usage and 'token_usage' in caption:
            result.setdefault('token_usage', {})['caption'] = caption['token_usage']
            total_cost += caption['token_usage'].get('estimated_cost_usd', 0)

    if include_token_usage:
        result['total_cost_usd'] = total_cost

    return result


def cleanup_temp_dir(temp_dir: str):
    """Clean up temporary directory"""
    try:
        shutil.rmtree(temp_dir)
        logger.debug(f"Cleaned up temp directory: {temp_dir}")
    except Exception as e:
        logger.warning(f"Failed to clean up {temp_dir}: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
