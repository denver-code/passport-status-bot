# Standard library imports
import asyncio
from collections import defaultdict, deque
from collections.abc import Awaitable, Callable
from datetime import datetime, timedelta
from typing import Any

# Third party imports
from aiogram import types
from aiogram.dispatcher.middlewares.base import BaseMiddleware

from bot.core.constants import (
    ANTISPAM_BAN_10MIN,
    ANTISPAM_BAN_30MIN,
    ANTISPAM_BANNED_MESSAGE,
    ANTISPAM_COMMAND_RUNNING,
    ANTISPAM_WAIT_MESSAGE,
    ANTISPAM_WAIT_WITH_WARNINGS,
    ANTISPAM_WARNING_MESSAGE,
    COMMAND_ERROR_MESSAGE,
    COMMAND_TIMEOUT_MESSAGE,
)

# Local application imports
from bot.core.logger import log_error, log_function, log_info
from bot.core.models.request_log import RequestLog
from bot.core.utils import get_user_id_str


def rate_limit(limit: int, key: str | None = None) -> Callable[..., Any]:
    """
    Decorator for rate limiting handlers.

    Args:
        limit: Maximum requests per time window
        key: Optional key for rate limiting (defaults to function name)
    """

    @log_function("rate_limit_decorator")
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        # Use type: ignore to suppress mypy warnings for dynamic attributes
        func.throttling_rate_limit = limit  # type: ignore[attr-defined]
        if key:
            func.throttling_key = key  # type: ignore[attr-defined]
        return func

    return decorator  # type: ignore[no-any-return]


class UserSpamTracker:
    """Track spam patterns for individual users."""

    def __init__(self) -> None:
        # Track recent messages per user (sliding window)
        self.user_messages: dict[int, deque] = defaultdict(lambda: deque(maxlen=20))
        # Track command patterns per user
        self.user_commands: dict[int, deque] = defaultdict(lambda: deque(maxlen=10))
        # Track warning levels per user
        self.user_warnings: dict[int, int] = defaultdict(int)
        # Track temporary bans per user
        self.user_bans: dict[int, datetime] = {}
        # Track repeated identical messages
        self.user_last_messages: dict[int, dict[str, datetime]] = defaultdict(dict)

    def is_spam_pattern(
        self, user_id: int, message_text: str, current_time: datetime
    ) -> bool:
        """Detect various spam patterns for a specific user."""

        # Pattern 1: Identical message repetition
        if message_text in self.user_last_messages[user_id]:
            last_time = self.user_last_messages[user_id][message_text]
            if (
                current_time - last_time
            ).total_seconds() < 10:  # Same message within 10 seconds
                return True

        # Pattern 2: Rapid message frequency (more than 5 messages in 30 seconds)
        recent_messages = [
            t
            for t in self.user_messages[user_id]
            if (current_time - t).total_seconds() <= 30
        ]
        if len(recent_messages) >= 5:
            return True

        # Pattern 3: Command flooding (more than 3 commands in 15 seconds)
        if message_text.startswith("/"):
            recent_commands = [
                t
                for t in self.user_commands[user_id]
                if (current_time - t).total_seconds() <= 15
            ]
            if len(recent_commands) >= 3:
                return True

        return False

    def record_message(
        self, user_id: int, message_text: str, current_time: datetime
    ) -> None:
        """Record a message for spam tracking."""
        self.user_messages[user_id].append(current_time)
        self.user_last_messages[user_id][message_text] = current_time

        if message_text.startswith("/"):
            self.user_commands[user_id].append(current_time)

    def escalate_warning(self, user_id: int) -> int:
        """Escalate warning level for a user and return new level."""
        self.user_warnings[user_id] += 1
        return self.user_warnings[user_id]

    def apply_temporary_ban(self, user_id: int, duration_minutes: int) -> None:
        """Apply a temporary ban to a user."""
        ban_until = datetime.utcnow() + timedelta(minutes=duration_minutes)
        self.user_bans[user_id] = ban_until
        log_info(f"User {user_id} temporarily banned until {ban_until}")

    def is_banned(self, user_id: int) -> tuple[bool, datetime | None]:
        """Check if user is currently banned."""
        if user_id not in self.user_bans:
            return False, None

        ban_until = self.user_bans[user_id]
        if datetime.utcnow() >= ban_until:
            # Ban expired, remove it
            del self.user_bans[user_id]
            return False, None

        return True, ban_until

    def reset_warnings(self, user_id: int) -> None:
        """Reset warnings for a user (good behavior)."""
        if self.user_warnings[user_id] > 0:
            self.user_warnings[user_id] = max(0, self.user_warnings[user_id] - 1)


class AntiSpamMiddleware(BaseMiddleware):
    """
    Advanced per-user antispam middleware with pattern detection and escalating penalties.
    """

    def __init__(
        self, base_limit: int = 3, window_seconds: int = 60, spam_detection: bool = True
    ):
        """
        Initialize the antispam middleware.

        Args:
            base_limit: Base rate limit per window
            window_seconds: Time window for rate limiting in seconds
            spam_detection: Enable advanced spam pattern detection
        """
        self.base_limit = base_limit
        self.window_seconds = window_seconds
        self.spam_detection = spam_detection

        # Per-user request tracking
        self.user_requests: dict[int, list[datetime]] = defaultdict(list)
        # Spam pattern tracker
        self.spam_tracker = UserSpamTracker() if spam_detection else None
        # Active command tasks per user
        self.user_active_tasks: dict[int, dict[str, asyncio.Task]] = defaultdict(dict)

        super().__init__()

    def _clean_old_requests(self, user_id: int, current_time: datetime) -> None:
        """Remove requests older than the time window for a specific user."""
        cutoff_time = current_time - timedelta(seconds=self.window_seconds)
        self.user_requests[user_id] = [
            req_time
            for req_time in self.user_requests[user_id]
            if req_time > cutoff_time
        ]

    def _get_user_rate_limit(self, user_id: int, base_limit: int) -> int:
        """Get dynamic rate limit for user based on their behavior."""
        if not self.spam_tracker:
            return base_limit

        warnings = self.spam_tracker.user_warnings[user_id]
        # Reduce rate limit for users with warnings
        if warnings >= 3:
            return max(1, base_limit // 3)
        elif warnings >= 2:
            return max(2, base_limit // 2)
        elif warnings >= 1:
            return max(2, int(base_limit * 0.75))

        return base_limit

    def _is_user_rate_limited(
        self, user_id: int, limit: int, current_time: datetime
    ) -> bool:
        """Check if specific user is rate limited."""
        self._clean_old_requests(user_id, current_time)
        return len(self.user_requests[user_id]) >= limit

    def _record_user_request(self, user_id: int, current_time: datetime) -> None:
        """Record a request for a specific user."""
        self.user_requests[user_id].append(current_time)

    async def _handle_spam_detection(
        self, event: types.Message, user_id: int, current_time: datetime
    ) -> str | None:
        """Handle spam detection and return appropriate response message."""
        if not self.spam_tracker:
            return None

        message_text = event.text or event.caption or ""

        # Check if user is banned
        is_banned, ban_until = self.spam_tracker.is_banned(user_id)
        if is_banned and ban_until is not None:
            remaining = (ban_until - current_time).total_seconds()
            minutes = int(remaining // 60)
            return ANTISPAM_BANNED_MESSAGE.format(minutes=minutes)

        # Check for spam patterns
        if self.spam_tracker.is_spam_pattern(user_id, message_text, current_time):
            warning_level = self.spam_tracker.escalate_warning(user_id)

            if warning_level >= 5:
                # Temporary ban for persistent spammers
                self.spam_tracker.apply_temporary_ban(user_id, 30)  # 30 minutes
                return ANTISPAM_BAN_30MIN
            elif warning_level >= 3:
                self.spam_tracker.apply_temporary_ban(user_id, 10)  # 10 minutes
                return ANTISPAM_BAN_10MIN
            else:
                return ANTISPAM_WARNING_MESSAGE.format(warning_level=warning_level)

        # Record message for future spam detection
        self.spam_tracker.record_message(user_id, message_text, current_time)

        # Reset warnings for good behavior (no spam in last 5 minutes)
        if warning_level := self.spam_tracker.user_warnings[user_id]:
            last_messages = list(self.spam_tracker.user_messages[user_id])
            if (
                last_messages
                and (current_time - last_messages[-1]).total_seconds() > 300
            ):
                self.spam_tracker.reset_warnings(user_id)

        return None

    async def __call__(
        self,
        handler: Callable[[types.TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: types.TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        """
        Process message with per-user antispam protection.
        """
        if not isinstance(event, types.Message) or not event.from_user:
            return await handler(event, data)

        user_id = event.from_user.id
        current_time = datetime.utcnow()

        # Log request asynchronously
        asyncio.create_task(self._log_request_async(event))

        # Bypass antiflood for admin user
        try:
            from bot.services import BotService

            if BotService.is_admin(user_id):
                return await handler(event, data)
        except Exception:
            # Fallback to direct settings check if service import fails
            try:
                from bot.core.config import settings

                if str(user_id) == str(settings.ADMIN_ID):
                    return await handler(event, data)
            except Exception as e:
                # Do not silently ignore unexpected failures
                try:
                    from bot.core.logger import log_warning

                    log_warning(f"Admin bypass fallback failed: {e}")
                except Exception:
                    # As a last resort, avoid breaking message handling
                    ...

        # Handle spam detection first
        if self.spam_detection:
            spam_message = await self._handle_spam_detection(
                event, user_id, current_time
            )
            if spam_message:
                try:
                    await event.answer(spam_message)
                except Exception as e:
                    log_error(
                        f"Failed to send spam warning to user {user_id}", user_id, e
                    )
                return None

        # Get user-specific rate limit
        base_limit = getattr(handler, "throttling_rate_limit", self.base_limit)
        user_limit = self._get_user_rate_limit(user_id, base_limit)

        # Check user-specific rate limiting
        if self._is_user_rate_limited(user_id, user_limit, current_time):
            try:
                warnings = (
                    self.spam_tracker.user_warnings[user_id] if self.spam_tracker else 0
                )
                if warnings > 0:
                    await event.answer(
                        ANTISPAM_WAIT_WITH_WARNINGS.format(warnings=warnings)
                    )
                else:
                    await event.answer(ANTISPAM_WAIT_MESSAGE)
            except Exception as e:
                from bot.core.logger import log_warning

                log_warning(f"Error answering user in rate limit: {e}")
            return None

        # Record this request for the user
        self._record_user_request(user_id, current_time)

        # Handle command execution with timeout
        key = getattr(
            handler,
            "throttling_key",
            handler.__name__ if hasattr(handler, "__name__") else "unknown",
        )
        task_key = f"{key}_{current_time.timestamp()}"

        # Check if user already has this command running
        if task_key in self.user_active_tasks[user_id]:
            try:
                await event.answer(ANTISPAM_COMMAND_RUNNING)
            except Exception as e:
                from bot.core.logger import log_warning

                log_warning(f"Error answering user for command running: {e}")
            return None

        # Create task for this user's command
        task = asyncio.create_task(
            self._handle_user_command_safely(handler, event, data, user_id, task_key)
        )
        self.user_active_tasks[user_id][task_key] = task

        # Clean up completed tasks for this user
        asyncio.create_task(self._cleanup_user_tasks(user_id))

        return await task

    async def _handle_user_command_safely(
        self,
        handler: Callable[[types.Message, dict[str, Any]], Awaitable[Any]],
        event: types.Message,
        data: dict[str, Any],
        user_id: int,
        task_key: str,
    ) -> Any:
        """Handle command execution safely for a specific user."""
        try:
            # Timeout based on user warnings (stricter for problem users)
            warnings = (
                self.spam_tracker.user_warnings[user_id] if self.spam_tracker else 0
            )
            timeout = max(30, 300 - (warnings * 60))  # 30s to 300s based on behavior

            return await asyncio.wait_for(handler(event, data), timeout=timeout)

        except TimeoutError:
            log_error(f"Command timeout for user {user_id}", user_id)
            try:
                await event.answer(COMMAND_TIMEOUT_MESSAGE)
            except Exception as e:
                from bot.core.logger import log_warning

                log_warning(f"Error answering user on timeout: {e}")
        except Exception as e:
            log_error(f"Command error for user {user_id}", user_id, e)
            try:
                await event.answer(COMMAND_ERROR_MESSAGE)
            except Exception as e2:
                from bot.core.logger import log_warning

                log_warning(f"Error answering user on command error: {e2}")
        finally:
            # Clean up user's task
            if task_key in self.user_active_tasks[user_id]:
                del self.user_active_tasks[user_id][task_key]

        return None

    async def _log_request_async(self, event: types.Message) -> None:
        """Asynchronously log the request without blocking."""
        try:
            if event.from_user:
                await RequestLog(
                    telegram_id=get_user_id_str(event), timestamp=datetime.utcnow()
                ).insert()
        except Exception as e:
            user_id = event.from_user.id if event.from_user else None
            log_error("Failed to log request", user_id, e)

    async def _cleanup_user_tasks(self, user_id: int) -> None:
        """Clean up completed tasks for a specific user."""
        try:
            completed_tasks = [
                key
                for key, task in self.user_active_tasks[user_id].items()
                if task.done()
            ]
            for key in completed_tasks:
                if key in self.user_active_tasks[user_id]:
                    del self.user_active_tasks[user_id][key]
        except Exception as e:
            log_error(f"Failed to cleanup tasks for user {user_id}", user_id, e)


# Aliases for backward compatibility
ThrottlingMiddleware = AntiSpamMiddleware
NonBlockingThrottlingMiddleware = AntiSpamMiddleware
