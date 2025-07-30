"""
Bot service layer for handling business logic.
Centralizes all bot-related operations and reduces redundancy.
"""

import asyncio
import datetime
import io
from collections import Counter
from pathlib import Path
from typing import Any, Optional, cast

import matplotlib.pyplot as plt
from aiogram import types
from aiogram.types import BufferedInputFile, FSInputFile

from bot.bot_instance import bot, get_bot_version, update_version
from bot.core.config import settings
from bot.core.constants import (
    BOT_STARTED_MESSAGE,
    BOT_STARTUP_FAILED,
    BOT_STOPPED_MESSAGE,
)
from bot.core.logger import log_error, log_info
from bot.core.models.application import ApplicationModel
from bot.core.models.push import PushModel
from bot.core.models.request_log import RequestLog
from bot.core.models.user import SubscriptionModel, UserModel
from bot.core.notify_admin import notify_admin


class BotService:
    """Service class for bot-related operations."""

    @staticmethod
    def is_admin(user_id: int) -> bool:
        """Check if user is admin."""
        return str(user_id) == str(settings.ADMIN_ID)

    @staticmethod
    def get_user_commands(is_admin: bool) -> list[types.BotCommand]:
        """Return the list of commands for a user depending on admin status."""
        from bot.core.command_registry import CommandRegistry

        return CommandRegistry.get_commands_for_user(is_admin)

    @staticmethod
    async def set_user_commands(user_id: int) -> None:
        """Set the list of commands for a user depending on admin status."""
        try:
            commands = BotService.get_user_commands(BotService.is_admin(user_id))
            await bot.set_my_commands(
                commands, scope=types.BotCommandScopeChat(chat_id=user_id)
            )
        except Exception as e:
            log_error(f"Failed to set user commands for {user_id}", user_id, e)


class StartupService:
    """Service for handling bot startup and shutdown."""

    @staticmethod
    async def startup() -> None:
        """Initialize bot on startup."""
        try:
            log_info("Bot startup initiated")

            # Set default commands
            commands = BotService.get_user_commands(is_admin=False)
            await bot.set_my_commands(commands)
            log_info("Bot commands set successfully")

            # Initialize database
            await DatabaseService.initialize()
            log_info("Database initialized successfully")

            # Notify admin
            await notify_admin(
                BOT_STARTED_MESSAGE.format(
                    timestamp=datetime.datetime.now().isoformat()
                )
            )
            log_info("Bot startup completed successfully")

        except Exception as e:
            log_error("Bot startup failed", exception=e)
            await notify_admin(BOT_STARTUP_FAILED.format(error=str(e)))
            raise

    @staticmethod
    async def shutdown() -> None:
        """Clean shutdown of bot."""
        try:
            log_info("Bot shutdown initiated")
            await notify_admin(
                BOT_STOPPED_MESSAGE.format(
                    timestamp=datetime.datetime.now().isoformat()
                )
            )
            log_info("Bot shutdown completed successfully")
        except Exception as e:
            log_error("Bot shutdown failed", exception=e)


class DatabaseService:
    """Service for database operations."""

    @staticmethod
    async def initialize() -> None:
        """Initialize database connection and models."""
        from beanie import init_beanie

        # Note: UpdateStrategy may not be available depending on Beanie version; avoid importing it
        from bot.core.database import db

        await init_beanie(
            database=cast(Any, db),
            document_models=[
                UserModel,
                SubscriptionModel,
                ApplicationModel,
                PushModel,
                RequestLog,
            ],
            recreate_views=False,
            allow_index_dropping=False,
        )


class LogService:
    """Service for log-related operations."""

    @staticmethod
    def read_log_tail(log_path: Path, lines: int = 50) -> str:
        """Read the last N lines from a log file."""
        if not log_path.exists():
            return ""

        with open(log_path, encoding="utf-8") as f:
            content = f.read()
            split_lines = content.split("\n")
            tail = split_lines[-lines:] if len(split_lines) > lines else split_lines
            return "\n".join(tail)

    @staticmethod
    async def get_logs_info() -> tuple[str | None, str | None]:
        """Get recent logs and error logs."""
        logs_dir = Path("logs")
        if not logs_dir.exists():
            return None, None

        from bot.core.logger import get_log_filename

        today_log = logs_dir / get_log_filename("bot")
        error_log = logs_dir / get_log_filename("errors")

        recent_content = None
        error_content = None

        if today_log.exists():
            recent_content = LogService.read_log_tail(today_log, 50)
            if len(recent_content) > 2000:
                recent_content = recent_content[-2000:]

        if error_log.exists():
            error_content = LogService.read_log_tail(error_log, 20)
            if error_content.strip() and len(error_content) > 2000:
                error_content = error_content[-2000:]

        return recent_content, error_content


class StatsService:
    """Service for statistics operations."""

    @staticmethod
    async def get_basic_stats() -> dict:
        """Get basic bot statistics."""
        user_count_task = UserModel.count()
        subscription_count_task = SubscriptionModel.count()
        request_count_task = RequestLog.count()

        user_count, subscription_count, request_count = await asyncio.gather(
            user_count_task, subscription_count_task, request_count_task
        )

        # Count errors from logs
        error_count = 0
        try:
            from bot.core.logger import get_log_filename

            error_log = Path("logs") / get_log_filename("errors")
            if error_log.exists():
                with open(error_log, encoding="utf-8") as f:
                    error_count = sum(1 for line in f if line.strip())
        except Exception as e:
            from bot.core.logger import log_warning

            log_warning(f"Error counting errors from logs: {e}")

        return {
            "users": user_count,
            "subscriptions": subscription_count,
            "requests": request_count,
            "errors": error_count,
        }

    @staticmethod
    async def generate_stats_graph() -> BufferedInputFile | None:
        """Generate statistics graph."""
        logs = await RequestLog.find_all().to_list()
        if not logs:
            return None

        days = [log.timestamp.date() for log in logs]
        counter = Counter(days)
        days_sorted = sorted(counter.keys())
        counts = [counter[day] for day in days_sorted]

        # Create plot
        plt.figure(figsize=(12, 6))
        plt.plot(days_sorted, counts, marker="o", linewidth=2, markersize=6)
        plt.title("Запити за днями", fontsize=14, fontweight="bold")
        plt.xlabel("Дата", fontsize=12)
        plt.ylabel("Кількість запитів", fontsize=12)
        plt.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        plt.tight_layout()

        # Save to buffer
        buf = io.BytesIO()
        plt.savefig(buf, format="png", dpi=150, bbox_inches="tight")
        buf.seek(0)

        photo_file = BufferedInputFile(buf.getvalue(), filename="stats_graph.png")
        buf.close()
        plt.close()

        return photo_file


class BroadcastService:
    """Service for broadcast operations."""

    @staticmethod
    def filter_broadcast_users(users: list, excepted_users: set) -> list:
        """Filter out admin and excepted users from the broadcast list."""
        return [
            user
            for user in users
            if (
                getattr(user, "telegram_id", None)
                and not BotService.is_admin(int(user.telegram_id))
                and str(user.telegram_id) not in excepted_users
            )
        ]

    @staticmethod
    async def send_broadcast_message(
        users: list, message: types.Message
    ) -> tuple[int, int, int]:
        """Send broadcast message to users, return (success, blocked, error) counts."""
        success_count = 0
        blocked_count = 0
        error_count = 0

        for i, user in enumerate(users):
            try:
                if message.reply_to_message:
                    await bot.copy_message(
                        user.telegram_id,
                        message.chat.id,
                        message.reply_to_message.message_id,
                    )
                    success_count += 1

                # Rate limiting
                if i > 0 and i % 30 == 0:
                    await asyncio.sleep(1)

            except Exception as e:
                err_str = str(e).lower()
                if "blocked" in err_str or "forbidden" in err_str:
                    blocked_count += 1
                else:
                    error_count += 1

                log_error(
                    f"Failed to send broadcast to user {getattr(user, 'telegram_id', 'unknown')}: {str(e)}"
                )

                # Log blocked users
                with open("out_blocked.txt", "a", encoding="utf-8") as f:
                    print(
                        f"User {getattr(user, 'telegram_id', 'unknown')} - {str(e)}",
                        file=f,
                    )

        return success_count, blocked_count, error_count


class VersionService:
    """Service for version-related operations."""

    @staticmethod
    async def get_version_info() -> tuple[str | None, str]:
        """Get current bot version and repository link."""
        await update_version()
        bot_version = await get_bot_version()

        from bot.bot_instance import bot_link

        return bot_version, bot_link
