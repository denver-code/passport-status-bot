"""
System-level commands available to all users.
"""

import datetime

from aiogram import types

from bot.core.constants import (
    AUTHORS_ERROR,
    AUTHORS_MESSAGE,
    BOT_PING_RESPONSE,
    BOT_TIME_RESPONSE,
    COMMAND_NOT_FOUND,
    HELP_MESSAGE,
    POLICY_MESSAGE,
    START_WELCOME_MESSAGE,
    VERSION_ERROR,
    VERSION_FORMAT,
    VERSION_UPDATE_ERROR,
)
from bot.core.logger import log_error, log_function, log_info
from bot.services import BotService, VersionService


class SystemCommands:
    """System commands available to all users."""

    @staticmethod
    @log_function("ping_command")
    async def ping(message: types.Message) -> None:
        """Respond to /ping command."""
        try:
            await message.answer(BOT_PING_RESPONSE)
        except Exception as e:
            user_id = message.from_user.id if message.from_user else None
            log_error("Ping command failed", user_id, e)

    @staticmethod
    @log_function("time_command")
    async def time(message: types.Message) -> None:
        """Respond to /time command with current server time."""
        try:
            await message.answer(
                BOT_TIME_RESPONSE.format(time=str(datetime.datetime.now()))
            )
        except Exception as e:
            user_id = message.from_user.id if message.from_user else None
            log_error("Time command failed", user_id, e)

    @staticmethod
    @log_function("start_command")
    async def start(message: types.Message) -> None:
        """Handle /start command."""
        try:
            if message.from_user:
                await BotService.set_user_commands(message.from_user.id)
            await message.answer(START_WELCOME_MESSAGE, parse_mode="Markdown")
        except Exception as e:
            user_id = message.from_user.id if message.from_user else None
            log_error("Start command failed", user_id, e)

    @staticmethod
    @log_function("help_command")
    async def help(message: types.Message) -> None:
        """Show help message with available commands."""
        try:
            await message.answer(HELP_MESSAGE, parse_mode="Markdown")
        except Exception as e:
            user_id = message.from_user.id if message.from_user else None
            log_error("Help command failed", user_id, e)

    @staticmethod
    @log_function("policy_command")
    async def policy(message: types.Message) -> None:
        """Send bot's privacy policy."""
        try:
            await message.answer(POLICY_MESSAGE, parse_mode="Markdown")
        except Exception as e:
            user_id = message.from_user.id if message.from_user else None
            log_error("Policy command failed", user_id, e)

    @staticmethod
    @log_function("authors_command")
    async def authors(message: types.Message) -> None:
        """Show information about bot authors."""
        try:
            bot_version, repo_link = await VersionService.get_version_info()
            version_text = bot_version if bot_version else "N/A"

            authors_text = AUTHORS_MESSAGE.format(
                version=version_text, repo_link=repo_link
            )

            await message.answer(
                authors_text, parse_mode="Markdown", disable_web_page_preview=True
            )
        except Exception as e:
            user_id = message.from_user.id if message.from_user else None
            log_error("Authors command failed", user_id, e)
            await message.answer(AUTHORS_ERROR)

    @staticmethod
    @log_function("version_command")
    async def version(message: types.Message) -> None:
        """Show bot version information."""
        try:
            bot_version, repo_link = await VersionService.get_version_info()
            log_info(f"Bot version: {bot_version}")

            version_text = (
                VERSION_FORMAT.format(version=bot_version, link=repo_link)
                if bot_version
                else VERSION_ERROR
            )

            await message.answer(
                version_text, parse_mode="Markdown", disable_web_page_preview=True
            )
        except Exception as e:
            user_id = message.from_user.id if message.from_user else None
            log_error("Version command failed", user_id, e)
            await message.answer(VERSION_UPDATE_ERROR)

    @staticmethod
    @log_function("command_not_found")
    async def command_not_found(message: types.Message) -> None:
        """Handle unrecognized commands."""
        try:
            command_text = ""
            if message.text:
                parts = message.text.split()
                if parts:
                    command_text = parts[0]
            await message.answer(COMMAND_NOT_FOUND.format(command=command_text))
        except Exception as e:
            user_id = message.from_user.id if message.from_user else None
            log_error("Command not found handler failed", user_id, e)
