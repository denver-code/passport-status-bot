import asyncio

import aiohttp
from aiogram import Bot

from bot.core.config import settings
from bot.core.logger import log_error, log_function, log_info

bot = Bot(token=settings.TOKEN.get_secret_value())

# Default values in case GitHub API is unavailable
DEFAULT_VERSION = "N/A"  # Changed from None to "N/A"
DEFAULT_LINK = "https://github.com/mrAlexZT/passport-status-bot/releases/latest"


@log_function("get_latest_release")
async def get_latest_release() -> tuple[str, str]:
    """
    Fetch latest release info from GitHub API.
    Returns tuple of (version, link).
    """
    try:
        async with aiohttp.ClientSession() as session:
            # Try to get latest release directly
            async with session.get(
                "https://api.github.com/repos/mrAlexZT/passport-status-bot/releases/latest",
                headers={
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
            ) as response:
                if response.status == 200:
                    latest = await response.json()
                    version = latest["tag_name"].lstrip("v")
                    link = latest["html_url"]
                    log_info(
                        f"Successfully fetched release info - Version: {version}, Link: {link}"
                    )
                    return version, link
                else:
                    log_error("Failed to fetch latest release", None, None)

                    # If latest release endpoint fails, try listing all releases
                    async with session.get(
                        "https://api.github.com/repos/mrAlexZT/passport-status-bot/releases",
                        headers={
                            "Accept": "application/vnd.github+json",
                            "X-GitHub-Api-Version": "2022-11-28",
                        },
                    ) as all_response:
                        if all_response.status == 200:
                            releases = await all_response.json()
                            if releases:
                                latest = releases[0]  # Get most recent release
                                version = latest["tag_name"].lstrip("v")
                                link = latest["html_url"]
                                return version, link
                            else:
                                log_error("No releases found", None, None)
                        else:
                            log_error("Failed to fetch all releases", None, None)
    except Exception as e:
        log_error(
            "Failed to fetch release info",
            None,
            e,  # Changed from formatted string to actual exception
        )

    return DEFAULT_VERSION, DEFAULT_LINK


# Initialize global variables
bot_version = DEFAULT_VERSION
bot_link = DEFAULT_LINK


# Update version and link asynchronously
@log_function("update_version")
async def update_version() -> tuple[str, str]:  # Fixed return type
    """Update version and link from GitHub."""
    global bot_version, bot_link
    log_info(f"Starting version update - Current version: {bot_version}")
    version, link = await get_latest_release()
    if version != "N/A":  # Only update if we got a valid version
        bot_version, bot_link = version, link
        log_info(f"Version updated successfully to {bot_version}")
    else:
        log_error(
            "Version update failed", None, None
        )  # Fixed: pass None instead of string
    return bot_version, bot_link


@log_function("version_check_loop")
async def version_check_loop() -> None:
    """Periodically check for new versions."""
    while True:
        await update_version()
        await asyncio.sleep(3600)  # Check every hour


@log_function("get_bot_version")
async def get_bot_version() -> str:
    """Get current bot version."""
    return bot_version if bot_version else DEFAULT_VERSION


# Note: Version updates will be scheduled through the main application's async context
