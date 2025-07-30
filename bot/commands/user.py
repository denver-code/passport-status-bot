"""
User management commands for profile and session handling.
"""

import cv2
import numpy as np
from aiogram import types
from PIL import Image
from qreader import QReader

from bot.core.api import Scraper
from bot.core.constants import (
    COMMAND_DUPLICATE_LINK,
    ERROR_CHECKING,
    ERROR_GENERIC_DETAILED,
    ERROR_QR_RECOGNITION,
    HEADER_YOUR_CABINET,
    LAST_UPDATE_FORMAT,
    QR_NOT_RECOGNIZED,
    QR_RECOGNIZED,
    SUCCESS_LINK_CREATED,
    SUCCESS_LINK_REMOVED,
    WAIT_CHECKING,
    WAIT_DATA_LOADING,
    WAIT_PHOTO_ANALYSIS,
)
from bot.core.logger import log_error, log_function
from bot.core.utils import (
    create_status_models_from_api_response,
    format_application_statuses_section,
    format_status_list,
    get_user_by_message,
    handle_invalid_session_id,
    handle_user_not_found,
    log_handler_error,
    safe_answer_message,
    safe_edit_message,
    show_typing_action,
    show_typing_and_wait_message,
)
from bot.services.user_service import CabinetManager, UserManager


class UserCommands:
    """Commands for user profile and session management."""

    @staticmethod
    @log_function("cabinet")
    async def cabinet(message: types.Message) -> None:
        """Show the user's cabinet with session and application status."""
        _message: types.Message | None = await show_typing_and_wait_message(
            message, WAIT_DATA_LOADING
        )
        if not _message:
            return

        try:
            cabinet_info = await CabinetManager.get_user_cabinet_info(message)
            if not cabinet_info:
                await handle_user_not_found(_message)
                return

            user = cabinet_info["user"]
            application = cabinet_info["application"]

            if message.from_user:
                initial_message = HEADER_YOUR_CABINET.format(
                    user_id=message.from_user.id, session_id=user.session_id
                )
            else:
                initial_message = "Error: Unable to get user information"

            await safe_edit_message(_message, initial_message, parse_mode="Markdown")

            if application:
                status_section = format_application_statuses_section(
                    application.statuses
                )
                last_update = LAST_UPDATE_FORMAT.format(
                    timestamp=application.last_update.strftime("%Y-%m-%d %H:%M")
                )

                msg_text = initial_message + "\n" + status_section + f"\n{last_update}"
                await safe_edit_message(_message, msg_text, parse_mode="Markdown")

        except Exception as e:
            user_id = message.from_user.id if message.from_user else None
            log_error("Cabinet command failed", user_id, e)

    @staticmethod
    @log_function("link")
    async def link(message: types.Message) -> None:
        """Link a Telegram user to a session ID."""
        _message: types.Message | None = await show_typing_and_wait_message(
            message, WAIT_CHECKING
        )
        if not _message:
            return

        try:
            parts = message.text.split(" ") if message.text else []
            if len(parts) != 2:
                await handle_invalid_session_id(_message, "/link")
                return

            session_id = parts[1]

            # Check if already linked
            user = await get_user_by_message(message)
            if user and user.session_id:
                await safe_edit_message(
                    _message, COMMAND_DUPLICATE_LINK.format(session_id=user.session_id)
                )
                return

            # Attempt to link
            success = await UserManager.link_user_to_session(message, session_id)
            if success:
                await safe_edit_message(
                    _message, SUCCESS_LINK_CREATED.format(session_id=session_id)
                )
            else:
                from bot.core.utils import handle_scraper_error

                await handle_scraper_error(_message)

        except Exception as e:
            user_id = message.from_user.id if message.from_user else None
            log_error("Link command failed", user_id, e)

    @staticmethod
    @log_function("unlink")
    async def unlink(message: types.Message) -> None:
        """Unlink a Telegram user from their session ID."""
        _message: types.Message | None = await show_typing_and_wait_message(
            message, WAIT_CHECKING
        )
        if not _message:
            return

        try:
            session_id = await UserManager.unlink_user(message)
            if session_id:
                await safe_edit_message(
                    _message, SUCCESS_LINK_REMOVED.format(session_id=session_id)
                )
            else:
                await handle_user_not_found(_message)

        except Exception as e:
            user_id = message.from_user.id if message.from_user else None
            log_error("Unlink command failed", user_id, e)

    @staticmethod
    @log_function("custom_check")
    async def custom_check(message: types.Message) -> None:
        """Check application status by ID and reply with formatted status list."""
        _message: types.Message | None = await safe_answer_message(
            message, WAIT_CHECKING
        )
        if not _message:
            return

        await show_typing_action(message)
        try:
            scraper = Scraper()
            session_id = message.text or ""
            status_data = scraper.check(session_id, retrive_all=True)
            if not status_data:
                await safe_edit_message(_message, ERROR_CHECKING)
                return

            statuses = create_status_models_from_api_response(status_data)
            formatted_text = format_status_list(statuses, session_id=session_id)

            await safe_edit_message(_message, formatted_text, parse_mode="Markdown")
        except Exception as e:
            log_handler_error("custom_check", message, e)
            await safe_edit_message(
                _message, ERROR_GENERIC_DETAILED.format(operation="перевірці")
            )

    @staticmethod
    @log_function("image_qr_recognition")
    async def image_qr_recognition(message: types.Message) -> None:
        """Recognize QR code from an image sent by the user."""
        _message: types.Message | None = await safe_answer_message(
            message, WAIT_PHOTO_ANALYSIS
        )
        if not _message:
            return

        await show_typing_action(message)
        try:
            if not (message.bot and message.photo):
                await safe_edit_message(_message, ERROR_QR_RECOGNITION)
                return

            file = await message.bot.get_file(message.photo[-1].file_id)
            if not file.file_path:
                await safe_edit_message(_message, ERROR_QR_RECOGNITION)
                return

            download_file = await message.bot.download_file(file.file_path)
            if not download_file:
                await safe_edit_message(_message, ERROR_QR_RECOGNITION)
                return

            # Open the image using PIL
            photo = Image.open(download_file)

            # Ensure the image is in RGB format
            image_np = np.array(photo)

            # Convert RGB to BGR for OpenCV
            image_processed = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)

            # Initialize the QR code reader and decode
            qr = QReader()

            # Handle the detection and decoding of QR codes
            detection_result = qr.detect_and_decode(image=image_processed)
            decoded: str | None = None

            if isinstance(detection_result, str):
                # Single QR code detected
                decoded = detection_result
            elif isinstance(detection_result, tuple) and len(detection_result) > 0:
                # Handle tuple case (multiple QR codes detected)
                decoded_items = detection_result[0]
                if decoded_items and len(decoded_items) > 0:
                    decoded = decoded_items[0]

            if decoded:
                await safe_edit_message(
                    _message, QR_RECOGNIZED.format(code=decoded), parse_mode="Markdown"
                )
            else:
                await safe_edit_message(_message, QR_NOT_RECOGNIZED)

        except Exception as e:
            log_handler_error("image_qr_recognition", message, e)
            await safe_edit_message(_message, ERROR_QR_RECOGNITION)
