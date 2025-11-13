from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import time
import asyncio
from app.config import settings
from app.api.routes import auth, ec2, guardduty, email, architecture
from app.database.dynamodb import DynamoDBConnection
from app.scheduler.notification_scheduler import notification_scheduler
from app.scheduler.critical_alert_monitor import critical_alert_monitor

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


    # Initialize multi-tenant worker registry
    app.state.client_workers = {}
    logger.info("Multi-tenant worker system initialized")
    logger.info(f"Worker collection interval: {settings.WORKER_COLLECTION_INTERVAL} seconds")

    # Start worker cleanup task
    async def cleanup_finished_workers():
        """Periodically remove finished worker tasks to prevent memory leaks"""
        while True:
            try:
                await asyncio.sleep(300)  # Every 5 minutes

                if hasattr(app.state, 'client_workers'):
                    finished = [
                        cid for cid, task in app.state.client_workers.items()
                        if task.done()
                    ]

                    for cid in finished:
                        logger.info(f"Cleaning up finished worker for {cid[:8]}...")
                        del app.state.client_workers[cid]

                    if finished:
                        logger.info(f"✓ Cleaned up {len(finished)} finished workers")
            except Exception as e:
                logger.error(f"Error in worker cleanup task: {e}", exc_info=True)

    app.state.cleanup_task = asyncio.create_task(cleanup_finished_workers())
    logger.info("Worker cleanup task started (runs every 5 minutes)")

    # Show startup summary
    logger.info("=" * 70)
    logger.info(f"{settings.APP_NAME} is ready!")
    logger.info(f"API: http://{settings.HOST}:{settings.PORT}")
    logger.info(f"Database: DynamoDB ({'connected' if db else 'disconnected'})")
    logger.info("=" * 70)
    notification_scheduler.start(hour=8, minute=0)
    logger.info("Daily notification scheduler started")

    critical_alert_monitor.start(interval_minutes=10)  # Every 10 minutes
    logger.info("Critical alert monitor started (every 10 minutes)")

    yield

    logger.info("Shutting down application")

    # Stop all client workers
    if hasattr(app.state, 'client_workers'):
        logger.info(f"Stopping {len(app.state.client_workers)} client workers...")
        for client_id, worker_task in list(app.state.client_workers.items()):
            try:
                if not worker_task.done():
                    worker_task.cancel()
                    logger.info(f"Stopped worker for {client_id[:8]}...")
            except Exception as e:
                logger.error(f"Error stopping worker: {e}")
        app.state.client_workers.clear()
        logger.info("All client workers stopped")

    # Stop cleanup task
    if hasattr(app.state, 'cleanup_task'):
        app.state.cleanup_task.cancel()
        try:
            await app.state.cleanup_task
        except asyncio.CancelledError:
            logger.info("Worker cleanup task stopped")

    notification_scheduler.stop()
    logger.info("Daily summary scheduler stopped")

    critical_alert_monitor.stop()
    logger.info("Critical alert monitor stopped")

    logger.info("=" * 60)
    logger.info("Shutdown complete")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan
)

# Add CORS middleware with explicit configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["Content-Type", "Authorization", "Accept", "Origin", "X-Requested-With"],
    expose_headers=["X-Process-Time"],
    max_age=3600,  # Cache preflight requests for 1 hour
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
app.include_router(architecture.router, prefix="/api/v1", tags=["Architecture"])


@app.get("/")
async def root():
    """Root endpoint with system status"""

    worker_count = 0
    if hasattr(app.state, 'client_workers'):
        worker_count = len(app.state.client_workers)

    return {
        "app": settings.APP_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "status": "running",
        "active_workers": worker_count
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        db = app.state.db
        db_healthy = await db.test_connection()
        worker_count = 0
        if hasattr(app.state, 'client_workers'):
            worker_count = len(app.state.client_workers)
        worker_status = f"{worker_count} active"

        return {
            "status": "healthy" if db_healthy else "unhealthy",
            "version": settings.VERSION,
            "environment": settings.ENVIRONMENT,
            "database": "connected" if db_healthy else "disconnected",
            "workers": worker_status,
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
    """Get detailed worker status for all clients"""

    if not hasattr(app.state, 'client_workers'):
        return {
            "enabled": False,
            "total_workers": 0,
            "status": "Worker system not initialized"
        }

    active_workers = sum(
        1 for task in app.state.client_workers.values()
        if not task.done()
    )

    return {
        "enabled": True,
        "total_workers": len(app.state.client_workers),
        "active_workers": active_workers,
        "collection_interval": settings.WORKER_COLLECTION_INTERVAL,
        "clients": [f"{cid[:8]}..." for cid in app.state.client_workers.keys()]
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