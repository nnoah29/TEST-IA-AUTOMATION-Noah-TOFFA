
import os
from dotenv import load_dotenv
from loguru import logger
from src.pipeline import Pipeline
from src.config import settings

load_dotenv()

def main():
    # Persist logs to file with daily rotation
    log_dir = "data/logs"
    os.makedirs(log_dir, exist_ok=True)
    logger.add(
        f"{log_dir}/pipeline_{{time:YYYY-MM-DD}}.log",
        rotation="1 day",
        retention="7 days",
        encoding="utf-8",
        level="INFO",
    )

    logger.info("Starting FANGA Document Processor...")
    logger.info(f"AI Provider: {settings.AI_PROVIDER} | Model: {settings.MODEL_NAME}")
    logger.info(f"Confidence threshold: {settings.CONFIDENCE_THRESHOLD}")

    os.makedirs(settings.INPUT_DIR, exist_ok=True)
    os.makedirs(settings.OUTPUT_DIR, exist_ok=True)

    try:
        pipeline = Pipeline()
        logger.info(f"Processing files from: {settings.INPUT_DIR}")
        pipeline.process_directory()
        logger.info("Processing complete. Report generated.")
    except Exception as e:
        logger.critical(f"Pipeline execution failed: {e}")

if __name__ == "__main__":
    main()
