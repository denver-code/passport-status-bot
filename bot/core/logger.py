"""
Enhanced logging module with structured logging and better error handling.
"""

import json
import logging
import sys
import traceback
from collections.abc import Callable
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Any, Union

from bot.core.config import settings


def get_log_filename(log_type: str = "bot") -> str:
    """Generate log filename with current date."""
    date_str = datetime.now().strftime("%Y%m%d")
    return f"{log_type}_{date_str}.log"


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured logging with JSON output."""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add user_id if present
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id

        # Add exception info if present
        if record.exc_info:
            exc_type, exc_value, exc_traceback = record.exc_info
            log_data["exception"] = {
                "type": exc_type.__name__ if exc_type else "Unknown",
                "message": str(exc_value),
                "traceback": traceback.format_exception(*record.exc_info),
            }

        return json.dumps(log_data, ensure_ascii=False)


class GlobalLogger:
    """Singleton logger with enhanced features and structured logging."""

    _instance: Union["GlobalLogger", None] = None
    _initialized: bool = False

    def __new__(cls) -> "GlobalLogger":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if not self._initialized:
            self.enabled: bool = True
            self.logger: logging.Logger = logging.getLogger("passport_bot")
            self.setup_logger()
            self._initialized = True

    def setup_logger(self) -> None:
        """Setup the logger with enhanced handlers and formatting."""
        self.logger.setLevel(logging.INFO)

        # Clear existing handlers
        if self.logger.hasHandlers():
            self.logger.handlers.clear()

        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)

        # Structured JSON file handler
        json_handler = logging.FileHandler(
            logs_dir / get_log_filename("structured"), encoding="utf-8"
        )
        json_handler.setLevel(logging.INFO)
        json_handler.setFormatter(StructuredFormatter())

        # Human-readable file handler
        file_handler = logging.FileHandler(
            logs_dir / get_log_filename("bot"), encoding="utf-8"
        )
        file_handler.setLevel(logging.INFO)

        # Error-only handler
        error_handler = logging.FileHandler(
            logs_dir / get_log_filename("errors"), encoding="utf-8"
        )
        error_handler.setLevel(logging.ERROR)

        # Console handler with colored output
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)

        # Enhanced formatter with more context
        detailed_formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(funcName)s() | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        file_handler.setFormatter(detailed_formatter)
        error_handler.setFormatter(detailed_formatter)
        console_handler.setFormatter(detailed_formatter)

        # Add handlers
        self.logger.addHandler(json_handler)
        self.logger.addHandler(file_handler)
        self.logger.addHandler(error_handler)
        self.logger.addHandler(console_handler)

    def _is_admin(self, user_id: int) -> bool:
        """Check if user is admin with proper import handling."""
        try:
            from bot.services import BotService

            return BotService.is_admin(user_id)
        except ImportError:
            # Fallback for backwards compatibility
            return str(user_id) == str(settings.ADMIN_ID)

    def toggle_logging(self, user_id: int) -> str:
        """Toggle logging on/off (admin only)."""
        if not self._is_admin(user_id):
            return "❌ Тільки адміністратор може керувати логуванням"

        self.enabled = not self.enabled
        status = "увімкнено" if self.enabled else "вимкнено"
        self.info(f"Logging toggled by admin {user_id}: {self.enabled}")
        return f"📊 Логування {status}"

    def _log_with_context(
        self,
        level: int,
        message: str,
        user_id: int | None = None,
        exception: Exception | None = None,
        extra: dict[str, Any] | None = None,
    ) -> None:
        """Internal method for logging with context."""
        if not self.enabled and level < logging.ERROR:
            return

        # Create extra context
        log_extra = extra or {}
        if user_id:
            log_extra["user_id"] = user_id

        # Format message with user context
        if user_id:
            formatted_message = f"[User: {user_id}] {message}"
        else:
            formatted_message = message

        # Log the message
        if exception:
            self.logger.log(
                level, formatted_message, exc_info=exception, extra=log_extra
            )
        else:
            self.logger.log(level, formatted_message, extra=log_extra)

    def info(self, message: str, user_id: int | None = None, **kwargs: Any) -> None:
        """Log info message with optional context."""
        self._log_with_context(logging.INFO, message, user_id, extra=kwargs)

    def error(
        self,
        message: str,
        user_id: int | None = None,
        exception: Exception | None = None,
        **kwargs: Any,
    ) -> None:
        """Log error message with exception details."""
        self._log_with_context(logging.ERROR, message, user_id, exception, extra=kwargs)

    def warning(self, message: str, user_id: int | None = None, **kwargs: Any) -> None:
        """Log warning message."""
        self._log_with_context(logging.WARNING, message, user_id, extra=kwargs)

    def debug(self, message: str, user_id: int | None = None, **kwargs: Any) -> None:
        """Log debug message."""
        self._log_with_context(logging.DEBUG, message, user_id, extra=kwargs)


# Global logger instance
global_logger = GlobalLogger()


def log_function(function_name: str) -> Callable[..., Any]:
    """Enhanced decorator for function logging with timing and error handling."""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = datetime.now()
            user_id = None

            # Try to extract user_id from arguments
            if args and hasattr(args[0], "from_user"):
                user_id = args[0].from_user.id

            global_logger.debug(
                f"Function {function_name} started",
                user_id=user_id,
                args_count=len(args),
                kwargs_keys=list(kwargs.keys()),
            )

            try:
                result = await func(*args, **kwargs)
                execution_time = (datetime.now() - start_time).total_seconds()

                global_logger.debug(
                    f"Function {function_name} completed successfully",
                    user_id=user_id,
                    execution_time=execution_time,
                )
                return result

            except Exception as e:
                execution_time = (datetime.now() - start_time).total_seconds()
                global_logger.error(
                    f"Function {function_name} failed",
                    user_id=user_id,
                    exception=e,
                    execution_time=execution_time,
                )
                raise

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = datetime.now()
            user_id = None

            if args and hasattr(args[0], "from_user"):
                user_id = args[0].from_user.id

            global_logger.debug(f"Function {function_name} started", user_id=user_id)

            try:
                result = func(*args, **kwargs)
                execution_time = (datetime.now() - start_time).total_seconds()

                global_logger.debug(
                    f"Function {function_name} completed successfully",
                    user_id=user_id,
                    execution_time=execution_time,
                )
                return result

            except Exception as e:
                execution_time = (datetime.now() - start_time).total_seconds()
                global_logger.error(
                    f"Function {function_name} failed",
                    user_id=user_id,
                    exception=e,
                    execution_time=execution_time,
                )
                raise

        # Return appropriate wrapper based on function type
        if hasattr(func, "__code__") and any(
            keyword in func.__code__.co_names for keyword in ["await", "async"]
        ):
            return async_wrapper
        return sync_wrapper

    return decorator


# Convenience functions
def log_info(message: str, user_id: int | None = None, **kwargs: Any) -> None:
    """Log info message."""
    global_logger.info(message, user_id, **kwargs)


def log_error(
    message: str,
    user_id: int | None = None,
    exception: Exception | None = None,
    **kwargs: Any,
) -> None:
    """Log error message."""
    global_logger.error(message, user_id, exception, **kwargs)


def log_warning(message: str, user_id: int | None = None, **kwargs: Any) -> None:
    """Log warning message."""
    global_logger.warning(message, user_id, **kwargs)


def log_debug(message: str, user_id: int | None = None, **kwargs: Any) -> None:
    """Log debug message."""
    global_logger.debug(message, user_id, **kwargs)
