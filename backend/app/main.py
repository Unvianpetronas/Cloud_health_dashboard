from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import time
import asyncio
from app.config import settings
from app.api.routes import auth, ec2, guardduty, email
from app.database.dynamodb import DynamoDBConnection
from app.worker import CloudHealthWorker


# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.APP_NAME} v{settings.VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug mode: {settings.DEBUG}")

    # Initialize database connection
    try:
        db = DynamoDBConnection()
        await db.test_connection()

        # Create tables if they don't exist
        if settings.ENVIRONMENT == "development":
            db.create_tables()
            logger.info("DynamoDB tables created/verified")

        app.state.db = db
        logger.info("Database connection established")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


    worker_task = None
    try:
        logger.info("Initializing background worker...")

        # Check if AWS credentials are configured
        worker = CloudHealthWorker()
        # Create background task for worker
        worker_task = asyncio.create_task(worker.start())
        app.state.worker_task = worker_task
        logger.info("Background worker started!")
        logger.info(f"Collection interval: {settings.METRICS_COLLECTION_INTERVAL} seconds")

    except Exception as e:
        logger.error(f"Warning: Could not start background worker: {e}")
        logger.info("API will continue without background data collection")

    # Show startup summary
    logger.info("=" * 70)
    logger.info(f"{settings.APP_NAME} is ready!")
    logger.info(f"API: http://{settings.HOST}:{settings.PORT}")
    logger.info(f"Database: DynamoDB ({'connected' if db else 'disconnected'})")
    logger.info(f"Worker: {'Running' if worker_task else 'Disabled'}")
    logger.info("=" * 70)

    yield


    logger.info("Shutting down application")


    if hasattr(app.state, 'worker_task') and app.state.worker_task:
        if not app.state.worker_task.done():
            logger.info("Stopping background worker...")
            app.state.worker_task.cancel()
            try:
                await app.state.worker_task
            except asyncio.CancelledError:
                logger.info("Background worker stopped")

    logger.info("Shutdown complete")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"] if not settings.DEBUG else ["*"],
    allow_headers=["Authorization", "Content-Type"] if not settings.DEBUG else ["*"],
)


# Add request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# Include routers
app.include_router(auth.router, prefix="/api/v1", tags=["Authentication"])
app.include_router(ec2.router, prefix="/api/v1", tags=["EC2"])
app.include_router(guardduty.router, prefix="/api/v1", tags=["GuardDuty"])
app.include_router(email.router, prefix="/api/v1", tags=["Email"])


@app.get("/")
async def root():
    """Root endpoint with system status"""
    worker_status = "disabled"
    if hasattr(app.state, 'worker_task') and app.state.worker_task:
        worker_status = "running" if not app.state.worker_task.done() else "stopped"

    return {
        "app": settings.APP_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "status": "running",
        "worker": worker_status
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        db = app.state.db
        db_healthy = await db.test_connection()
        worker_running = False
        worker_status = "disabled"
        if hasattr(app.state, 'worker_task') and app.state.worker_task:
            worker_running = not app.state.worker_task.done()
            worker_status = "running" if worker_running else "stopped"

        return {
            "status": "healthy" if db_healthy else "unhealthy",
            "version": settings.VERSION,
            "environment": settings.ENVIRONMENT,
            "database": "connected" if db_healthy else "disconnected",
            "worker": worker_status,
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": time.time()
        }



@app.get("/api/v1/worker/status")
async def get_worker_status():
    """Get detailed worker status"""
    if not hasattr(app.state, 'worker_task') or not app.state.worker_task:
        return {
            "enabled": False,
            "running": False,
            "status": "disabled",
            "message": "Worker is not initialized (check AWS credentials)"
        }

    worker_running = not app.state.worker_task.done()

    return {
        "enabled": True,
        "running": worker_running,
        "status": "running" if worker_running else "stopped",
        "collection_interval": settings.METRICS_COLLECTION_INTERVAL,
        "region": settings.YOUR_AWS_REGION
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )