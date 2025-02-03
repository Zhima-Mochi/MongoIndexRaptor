import logging

# Constants
DEFAULT_CONFIG = {
    "connection": "mongodb://localhost:27017",
    "iterations": 1000,
    "warmup_iterations": 10,
    "sample_interval": 1,
    "output_format": "table",
    "max_retries": 3,
    "retry_delay_base": 2,  # Base for exponential backoff
}

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)
