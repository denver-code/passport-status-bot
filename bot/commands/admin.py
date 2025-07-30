"""
Administrative commands for bot management.
"""

from aiogram import types
from aiogram.types import FSInputFile

from bot.core.constants import (
    ADMIN_CLEANUP_ANALYZING,
    ADMIN_CLEANUP_CANCEL_BUTTON,
    ADMIN_CLEANUP_CANCELLED,
    ADMIN_CLEANUP_CANCELLED_POPUP,
    ADMIN_CLEANUP_CONFIRM,
    ADMIN_CLEANUP_CONFIRM_BUTTON,
    ADMIN_CLEANUP_ERROR,
    ADMIN_CLEANUP_EXPIRED,
    ADMIN_CLEANUP_NO_PERMISSION,
    ADMIN_CLEANUP_NOTHING,
    ADMIN_CLEANUP_PROCESSING,
    ADMIN_CLEANUP_RESULT,
    ADMIN_CLEANUP_START,
    ADMIN_INVALID_DATA_WARNING,
    ADMIN_TOTAL_STATS,
    ADMIN_USER_ENTRY,
    ADMIN_USER_NO_SUBSCRIPTIONS,
    ADMIN_USER_SESSION,
    ADMIN_USER_SUBSCRIPTION_ENTRY,
    ADMIN_USER_SUBSCRIPTIONS_HEADER,
    ADMIN_USERS_LIST_HEADER,
    BROADCAST_ERROR,
    BROADCAST_NO_REPLY,
    BROADCAST_PROGRESS,
    BROADCAST_RESULT,
    ERROR_GENERIC,
    FILE_ERROR,
    FILE_NOT_FOUND,
    LOGGING_ERROR_MESSAGE,
    LOGS_ERROR,
    LOGS_ERROR_HEADER,
    LOGS_NO_ERRORS,
    LOGS_NOT_FOUND,
    LOGS_RECENT_HEADER,
    STATS_ERROR,
    STATS_GRAPH_ERROR,
    STATS_GRAPH_NO_DATA,
    STATS_GRAPH_PROGRESS,
    STATS_MESSAGE,
)
from bot.core.logger import global_logger, log_error, log_function, log_info
from bot.core.models.user import SubscriptionModel, UserModel
from bot.core.utils import (
    admin_permission_check,
    safe_edit_message,
    safe_edit_message_markdown,
    show_typing_and_wait_message,
)
from bot.services import BroadcastService, LogService, StatsService


class AdminCommands:
    """Administrative commands for bot management."""

    @staticmethod
    @log_function("toggle_logging")
    async def toggle_logging(message: types.Message) -> None:
        """Admin command to enable/disable logging."""
        if not await admin_permission_check(message):
            return

        try:
            user_id = message.from_user.id if message.from_user else None
            if user_id:
                result = global_logger.toggle_logging(user_id)
                await message.answer(result)
            else:
                await message.answer(LOGGING_ERROR_MESSAGE)
        except Exception as e:
            user_id = message.from_user.id if message.from_user else None
            log_error("Toggle logging command failed", user_id, e)
            await message.answer(LOGGING_ERROR_MESSAGE)

    @staticmethod
    @log_function("get_logs")
    async def get_logs(message: types.Message) -> None:
        """Admin command to get recent logs."""
        if not await admin_permission_check(message):
            return

        try:
            recent_content, error_content = await LogService.get_logs_info()

            if recent_content is None:
                await message.answer(LOGS_NOT_FOUND)
                return

            if recent_content:
                await message.answer(
                    LOGS_RECENT_HEADER.format(content=recent_content),
                    parse_mode="Markdown",
                )

            if error_content and error_content.strip():
                await message.answer(
                    LOGS_ERROR_HEADER.format(content=error_content),
                    parse_mode="Markdown",
                )
            else:
                await message.answer(LOGS_NO_ERRORS)

        except Exception as e:
            user_id = message.from_user.id if message.from_user else None
            log_error("Get logs command failed", user_id, e)
            await message.answer(LOGS_ERROR)

    @staticmethod
    @log_function("broadcast_command")
    async def broadcast(message: types.Message) -> None:
        """Admin command to broadcast a message to all users."""
        if not await admin_permission_check(message):
            return

        try:
            if not message.reply_to_message:
                await message.answer(BROADCAST_NO_REPLY)
                return

            args = (
                message.text.split()[1:]
                if message.text and len(message.text.split()) > 1
                else []
            )
            excepted_users = set(args)

            users = await UserModel.all().to_list()
            filtered_users = BroadcastService.filter_broadcast_users(
                users, excepted_users
            )

            user_id = message.from_user.id if message.from_user else None
            log_info(
                f"Broadcasting message to {len(filtered_users)} users, excluding {len(excepted_users)} users"
            )

            progress_msg = None
            if len(filtered_users) > 100:
                progress_msg = await message.answer(
                    BROADCAST_PROGRESS.format(count=len(filtered_users))
                )

            (
                success_count,
                blocked_count,
                error_count,
            ) = await BroadcastService.send_broadcast_message(filtered_users, message)

            result_text = BROADCAST_RESULT.format(
                success=success_count, blocked=blocked_count, error=error_count
            )

            if progress_msg:
                await progress_msg.edit_text(result_text)
            else:
                await message.answer(result_text)

            log_info(
                f"Broadcast completed: {success_count} sent, {blocked_count} blocked, {error_count} errors"
            )

        except Exception as e:
            user_id = message.from_user.id if message.from_user else None
            log_error("Broadcast command failed", user_id, e)
            await message.answer(BROADCAST_ERROR)

    @staticmethod
    @log_function("get_out_txt_command")
    async def get_out_txt(message: types.Message) -> None:
        """Admin command to send the out.txt file."""
        if not await admin_permission_check(message):
            return

        try:
            await message.answer_document(FSInputFile("out.txt"))
        except FileNotFoundError:
            await message.answer(FILE_NOT_FOUND.format(filename="out.txt"))
        except Exception as e:
            user_id = message.from_user.id if message.from_user else None
            log_error("Get out.txt command failed", user_id, e)
            await message.answer(FILE_ERROR)

    @staticmethod
    @log_function("stats_command")
    async def stats(message: types.Message) -> None:
        """Admin command to show bot statistics."""
        if not await admin_permission_check(message):
            return

        try:
            stats_data = await StatsService.get_basic_stats()
            await message.answer(STATS_MESSAGE.format(**stats_data))
        except Exception as e:
            user_id = message.from_user.id if message.from_user else None
            log_error("Stats command failed", user_id, e)
            await message.answer(STATS_ERROR)

    @staticmethod
    @log_function("stats_graph_command")
    async def stats_graph(message: types.Message) -> None:
        """Admin command to show the statistics graph."""
        if not await admin_permission_check(message):
            return

        try:
            progress_msg = await message.answer(STATS_GRAPH_PROGRESS)

            photo_file = await StatsService.generate_stats_graph()
            if not photo_file:
                await progress_msg.edit_text(STATS_GRAPH_NO_DATA)
                return

            await progress_msg.delete()

            from bot.core.models.request_log import RequestLog

            logs = await RequestLog.find_all().to_list()
            days = {log.timestamp.date() for log in logs}

            await message.answer_photo(
                photo=photo_file,
                caption=f"📊 Графік запитів за період\n📅 Всього днів: {len(days)}\n📨 Всього запитів: {len(logs)}",
            )

        except Exception as e:
            user_id = message.from_user.id if message.from_user else None
            log_error("Stats graph command failed", user_id, e)
            await message.answer(STATS_GRAPH_ERROR)

    @staticmethod
    @log_function("users_list")
    async def users_list(message: types.Message) -> None:
        """Show list of all users and their subscriptions (admin only)."""
        if not await admin_permission_check(message):
            return

        _message = await show_typing_and_wait_message(
            message, "Завантаження даних користувачів..."
        )
        if not _message:
            return

        try:
            from typing import Any

            users_collection: Any = UserModel.get_pymongo_collection()
            subs_collection: Any = SubscriptionModel.get_pymongo_collection()

            users = await users_collection.find({}).to_list(length=None)
            subscriptions = await subs_collection.find({}).to_list(length=None)

            # Group subscriptions by user
            user_subscriptions: dict[str, list[str]] = {}
            invalid_subs = []
            for sub in subscriptions:
                telegram_id = sub.get("telegram_id")
                session_id = sub.get("session_id")
                if not telegram_id or not session_id:
                    invalid_subs.append(sub)
                    continue
                user_subscriptions.setdefault(telegram_id, []).append(session_id)

            if invalid_subs:
                user_id = message.from_user.id if message.from_user else None
                log_error("Found invalid subscriptions", user_id, None)

            # Format message
            msg_lines = [ADMIN_USERS_LIST_HEADER]
            invalid_users = []

            for user in users:
                telegram_id = user.get("telegram_id")
                session_id = user.get("session_id", "Не встановлено")
                if not telegram_id:
                    invalid_users.append(user)
                    continue

                user_subs = user_subscriptions.get(telegram_id, [])

                msg_lines.append(ADMIN_USER_ENTRY.format(telegram_id=telegram_id))
                msg_lines.append(ADMIN_USER_SESSION.format(session_id=session_id))

                if user_subs:
                    msg_lines.append(ADMIN_USER_SUBSCRIPTIONS_HEADER)
                    for sub_id in user_subs:
                        msg_lines.append(
                            ADMIN_USER_SUBSCRIPTION_ENTRY.format(sub_id=sub_id)
                        )
                else:
                    msg_lines.append(ADMIN_USER_NO_SUBSCRIPTIONS)
                msg_lines.append("")

            if invalid_users:
                user_id = message.from_user.id if message.from_user else None
                log_error("Found invalid users", user_id, None)

            valid_users = len(users) - len(invalid_users)
            valid_subs = len(subscriptions) - len(invalid_subs)

            msg_lines.append(
                ADMIN_TOTAL_STATS.format(users=valid_users, subs=valid_subs)
            )
            if invalid_users or invalid_subs:
                msg_lines.append(
                    ADMIN_INVALID_DATA_WARNING.format(
                        invalid_users=len(invalid_users), invalid_subs=len(invalid_subs)
                    )
                )

            await safe_edit_message_markdown(_message, "\n".join(msg_lines))

        except Exception as e:
            user_id = message.from_user.id if message.from_user else None
            log_error("users_list failed", user_id, e)
            await safe_edit_message(_message, ERROR_GENERIC)

    @staticmethod
    @log_function("cleanup_db")
    async def cleanup_db(message: types.Message) -> None:
        """Remove invalid data from the database (admin only)."""
        if not await admin_permission_check(message):
            return

        _message = await show_typing_and_wait_message(message, ADMIN_CLEANUP_START)
        if not _message:
            return

        try:
            from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

            await _message.edit_text(ADMIN_CLEANUP_ANALYZING, parse_mode="Markdown")
            users_to_delete, subs_to_delete, stats = await AdminCommands._analyze_db(
                _message
            )

            if not users_to_delete and not subs_to_delete:
                await safe_edit_message_markdown(_message, ADMIN_CLEANUP_NOTHING)
                return

            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text=ADMIN_CLEANUP_CONFIRM_BUTTON,
                            callback_data=f"cleanup_confirm_{len(users_to_delete)}_{len(subs_to_delete)}",
                        ),
                        InlineKeyboardButton(
                            text=ADMIN_CLEANUP_CANCEL_BUTTON,
                            callback_data="cleanup_cancel",
                        ),
                    ]
                ]
            )

            await _message.edit_text(
                ADMIN_CLEANUP_CONFIRM.format(
                    users=len(users_to_delete), subs=len(subs_to_delete), **stats
                ),
                reply_markup=keyboard,
                parse_mode="Markdown",
            )

        except Exception as e:
            user_id = message.from_user.id if message.from_user else None
            log_error("cleanup_db failed", user_id, e)
            await safe_edit_message(_message, ADMIN_CLEANUP_ERROR)

    @staticmethod
    @log_function("cleanup_callback")
    async def cleanup_callback(callback_query: types.CallbackQuery) -> None:
        """Handle cleanup confirmation callback."""
        message = callback_query.message

        if not await admin_permission_check(callback_query):
            await callback_query.answer(ADMIN_CLEANUP_NO_PERMISSION)
            return

        if not message or not isinstance(message, types.Message):
            return

        try:
            if not callback_query.data:
                return

            parts = callback_query.data.split("_")
            action = parts[1]

            if action == "cancel":
                current_text = message.text or ""
                await message.edit_text(
                    current_text + "\n\n" + ADMIN_CLEANUP_CANCELLED,
                    parse_mode="Markdown",
                )
                await callback_query.answer(ADMIN_CLEANUP_CANCELLED_POPUP)
                return

            expected_users = int(parts[2])
            expected_subs = int(parts[3])

            await callback_query.answer(ADMIN_CLEANUP_PROCESSING)
            await message.edit_text(ADMIN_CLEANUP_ANALYZING, parse_mode="Markdown")

            users_to_delete, subs_to_delete, stats = await AdminCommands._analyze_db(
                message
            )

            if (
                len(users_to_delete) != expected_users
                or len(subs_to_delete) != expected_subs
            ):
                await message.edit_text(ADMIN_CLEANUP_EXPIRED, parse_mode="Markdown")
                return

            await message.edit_text("🗑 Видалення даних...", parse_mode="Markdown")

            (
                total_users_deleted,
                total_subs_deleted,
            ) = await AdminCommands._perform_cleanup(
                users_to_delete, subs_to_delete, message
            )

            await message.edit_text(
                ADMIN_CLEANUP_RESULT.format(
                    users=total_users_deleted, subs=total_subs_deleted, **stats
                ),
                parse_mode="Markdown",
            )

        except Exception as e:
            user_id = callback_query.from_user.id if callback_query.from_user else None
            log_error("cleanup_callback failed", user_id, e)
            if message:
                await message.edit_text(ADMIN_CLEANUP_ERROR, parse_mode="Markdown")

    @staticmethod
    async def _analyze_db(message: types.Message | None = None) -> tuple:
        """Analyze database for invalid records."""
        from typing import Any

        users_collection: Any = UserModel.get_pymongo_collection()
        subs_collection: Any = SubscriptionModel.get_pymongo_collection()

        users = await users_collection.find({}).to_list(length=None)
        subscriptions = await subs_collection.find({}).to_list(length=None)

        stats = {
            "users_no_id": 0,
            "users_invalid": 0,
            "subs_no_id": 0,
            "subs_no_session": 0,
            "subs_orphaned": 0,
        }

        users_to_delete = []
        valid_user_ids = set()

        for user in users:
            telegram_id = user.get("telegram_id")
            if not telegram_id:
                users_to_delete.append(user["_id"])
                stats["users_no_id"] += 1
                continue

            valid_user_ids.add(telegram_id)

            if not user.get("session_id"):
                users_to_delete.append(user["_id"])
                stats["users_invalid"] += 1
                continue

        subs_to_delete = []

        for sub in subscriptions:
            telegram_id = sub.get("telegram_id")
            session_id = sub.get("session_id")

            if not telegram_id:
                subs_to_delete.append(sub["_id"])
                stats["subs_no_id"] += 1
                continue

            if not session_id:
                subs_to_delete.append(sub["_id"])
                stats["subs_no_session"] += 1
                continue

            if telegram_id not in valid_user_ids:
                subs_to_delete.append(sub["_id"])
                stats["subs_orphaned"] += 1
                continue

        return users_to_delete, subs_to_delete, stats

    @staticmethod
    async def _perform_cleanup(
        users_to_delete: list,
        subs_to_delete: list,
        message: types.Message | None = None,
    ) -> tuple:
        """Actually delete the invalid records."""
        from typing import Any

        users_collection: Any = UserModel.get_pymongo_collection()
        subs_collection: Any = SubscriptionModel.get_pymongo_collection()

        total_users_deleted = 0
        total_subs_deleted = 0

        if users_to_delete:
            result = await users_collection.delete_many(
                {"_id": {"$in": users_to_delete}}
            )
            total_users_deleted = result.deleted_count

        if subs_to_delete:
            result = await subs_collection.delete_many({"_id": {"$in": subs_to_delete}})
            total_subs_deleted = result.deleted_count

        return total_users_deleted, total_subs_deleted
