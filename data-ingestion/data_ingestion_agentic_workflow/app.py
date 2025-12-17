import asyncio
import atexit
import logging

from cezzis_kafka import shutdown_consumers
from cezzis_otel import shutdown_otel

# Application specific imports
from data_ingestion_agentic_workflow.agents import run_chunking_agent, run_embedding_agent, run_extraction_agent
from data_ingestion_agentic_workflow.behaviors.otel import initialize_opentelemetry

logger: logging.Logger = logging.getLogger("main")


async def main() -> None:
    """Main function to run the cocktails data ingestion agentic workflow."""
    global logger

    initialize_opentelemetry()

    logger = logging.getLogger("main")
    logger.info("Starting Cocktail Ingestion Agentic Workflow...")

    try:
        await asyncio.gather(
            run_extraction_agent(),
            run_chunking_agent(),
            run_embedding_agent(),
        )
    except asyncio.CancelledError:
        logger.info("Application cancelled")
    except Exception as e:
        logger.error("Application error", exc_info=True, extra={"error": str(e)})
        raise


if __name__ == "__main__":
    atexit.register(shutdown_otel)

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received. Shutting down...")
    finally:
        shutdown_consumers()
