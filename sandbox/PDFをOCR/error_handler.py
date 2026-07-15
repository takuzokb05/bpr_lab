"""
Error handling and retry logic for API calls
"""

import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Callable, Any, Optional
from functools import wraps


class OCRError(Exception):
    """Base exception for OCR errors"""
    pass


class APIError(OCRError):
    """API-related errors"""
    pass


class ProcessingError(OCRError):
    """Processing-related errors"""
    pass


class ErrorHandler:
    """Handles errors and retry logic"""
    
    def __init__(self, max_retries: int = 3, log_dir: str = "logs"):
        """
        Initialize error handler
        
        Args:
            max_retries: Maximum number of retries (default: 3)
            log_dir: Directory for error logs
        """
        self.max_retries = max_retries
        self.log_dir = log_dir
        
        # Create log directory
        Path(log_dir).mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        self._setup_logging()
    
    def _setup_logging(self) -> None:
        """Setup logging configuration"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = Path(self.log_dir) / f"error_{timestamp}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger(__name__)
    
    def retry_with_backoff(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with exponential backoff retry
        
        Args:
            func: Function to execute
            *args: Positional arguments for function
            **kwargs: Keyword arguments for function
        
        Returns:
            Function result
        
        Raises:
            APIError: If all retries failed
        """
        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
                
            except Exception as e:
                wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                
                if attempt < self.max_retries - 1:
                    self.logger.warning(
                        f"Attempt {attempt + 1}/{self.max_retries} failed: {e}. "
                        f"Retrying in {wait_time}s..."
                    )
                    time.sleep(wait_time)
                else:
                    self.logger.error(f"All {self.max_retries} attempts failed: {e}")
                    raise APIError(f"Failed after {self.max_retries} retries: {e}")
    
    def log_error(self, page: int, error: Exception, resume_command: str = "") -> None:
        """
        Log error in user-friendly format
        
        Args:
            page: Page number where error occurred
            error: Exception that occurred
            resume_command: Command to resume processing
        """
        error_type = type(error).__name__
        error_msg = str(error)
        
        if not resume_command:
            resume_command = "python main.py --resume"
        
        log_message = f"[Page {page}]: [{error_type}]: {error_msg}\nResume with: {resume_command}"
        
        self.logger.error(log_message)
        print(f"\n❌ Error occurred:\n{log_message}\n")
    
    def handle_api_error(self, error: Exception, page: int) -> None:
        """
        Handle API-specific errors with helpful messages
        
        Args:
            error: Exception from API call
            page: Page number being processed
        """
        error_str = str(error).lower()
        
        if "rate limit" in error_str or "quota" in error_str:
            self.log_error(
                page,
                error,
                "Wait for rate limit reset, then: python main.py --resume"
            )
        elif "invalid" in error_str and "api" in error_str:
            self.log_error(
                page,
                error,
                "Check API_KEY.txt and run: python main.py --resume"
            )
        elif "timeout" in error_str:
            self.log_error(
                page,
                error,
                "Check network connection, then: python main.py --resume"
            )
        else:
            self.log_error(page, error)


def with_retry(max_retries: int = 3):
    """
    Decorator for automatic retry with exponential backoff
    
    Args:
        max_retries: Maximum number of retries
    
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt
                        print(f"⚠️ Retry {attempt + 1}/{max_retries} after {wait_time}s...")
                        time.sleep(wait_time)
                    else:
                        raise
            return None
        return wrapper
    return decorator
