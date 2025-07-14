from celery import shared_task
# Import the correct function name from ai_logic.py
from .ai_logic import process_request
from .Agents.logging_config import AppLogger

logger = AppLogger(log_file='tasks_debug.log').get_logger()

@shared_task
def process_user_query_task(user_query: str):
    """Celery task to handle text-based queries from the user."""
    logger.info(f"Starting chat task for query: {user_query}")
    # Use the new function name here
    result = process_request(user_input=user_query)
    logger.info(f"Task finished for query: {user_query}")
    return result.model_dump()

@shared_task
def process_profile_form_task(user_query: str):
    """
    Celery task to handle profile form submissions.
    The user_query is expected to be 'Save Gathered Data'.
    The actual data is read from a temporary file by the AI logic.
    """
    logger.info("Starting form submission task.")
    # The user_query is now "Save Gathered Data".
    # The process_request function will handle this query.
    result = process_request(user_input=user_query)
    logger.info("Task finished for form submission.")
    return result.model_dump()