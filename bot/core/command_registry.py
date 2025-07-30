"""
Command registry for centralized command management.
"""

from typing import TYPE_CHECKING

from aiogram import types

if TYPE_CHECKING:
    pass

registered_commands: list[str] = []


class CommandRegistry:
    """Registry for bot commands with role-based access."""

    # Define all available commands
    ALL_COMMANDS = [
        types.BotCommand(command="/start", description="Почати роботу з ботом"),
        types.BotCommand(command="/help", description="Допомога"),
        types.BotCommand(command="/authors", description="Інформація про авторів"),
        types.BotCommand(
            command="/policy", description="Політика бота та конфіденційність"
        ),
        types.BotCommand(command="/cabinet", description="Персональний кабінет"),
        types.BotCommand(command="/link", description="Прив'язати ідентифікатор"),
        types.BotCommand(
            command="/unlink",
            description="Відв'язати ідентифікатор та видалити профіль",
        ),
        types.BotCommand(command="/subscribe", description="Підписатися на сповіщення"),
        types.BotCommand(
            command="/unsubscribe", description="Відписатися від сповіщень"
        ),
        types.BotCommand(command="/subscriptions", description="Список підписок"),
        types.BotCommand(command="/update", description="Оновити статус заявки вручну"),
        types.BotCommand(
            command="/push", description="Підписатися на сповіщення через NTFY.sh"
        ),
        types.BotCommand(
            command="/dump",
            description="Отримати весь дамп доступних даних на ваші підписки",
        ),
        types.BotCommand(command="/ping", description="Перевірити чи працює бот"),
        types.BotCommand(command="/time", description="Поточний час сервера"),
        types.BotCommand(command="/version", description="Версія бота"),
        types.BotCommand(command="/broadcast", description="Розсилка"),
        types.BotCommand(command="/get_out_txt", description="Отримати out.txt"),
        types.BotCommand(command="/stats", description="Статистика"),
        types.BotCommand(command="/stats_graph", description="Графік запитів"),
        types.BotCommand(
            command="/toggle_logging", description="Увімкнути/вимкнути логування"
        ),
        types.BotCommand(command="/logs", description="Переглянути логи"),
        types.BotCommand(command="/users", description="Список користувачів"),
        types.BotCommand(command="/cleanup", description="Очистити базу даних"),
    ]

    # Admin-only commands
    ADMIN_ONLY_COMMANDS = {
        "/broadcast",
        "/get_out_txt",
        "/stats",
        "/stats_graph",
        "/toggle_logging",
        "/logs",
        "/users",
        "/cleanup",
    }

    @classmethod
    def get_commands_for_user(cls, is_admin: bool) -> list[types.BotCommand]:
        """Get commands available for a specific user role."""
        if is_admin:
            return cls.ALL_COMMANDS

        return [
            cmd
            for cmd in cls.ALL_COMMANDS
            if cmd.command not in cls.ADMIN_ONLY_COMMANDS
        ]

    @classmethod
    def is_valid_command(cls, command: str) -> bool:
        """Check if a command is valid."""
        return any(cmd.command == command for cmd in cls.ALL_COMMANDS)

    @classmethod
    def is_admin_command(cls, command: str) -> bool:
        """Check if a command requires admin privileges."""
        return command in cls.ADMIN_ONLY_COMMANDS
