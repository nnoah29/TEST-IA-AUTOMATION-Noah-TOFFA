
import os
from dotenv import load_dotenv
from loguru import logger
from src.pipeline import Pipeline
from src.config import settings

load_dotenv()

def main():
    logger.info("Starting FANGA Document Processor...")
    
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
