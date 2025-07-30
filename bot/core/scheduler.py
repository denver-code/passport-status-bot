from bot.core.api import Scraper
from bot.core.logger import log_function
from bot.core.models.application import ApplicationModel
from bot.core.notificator import notify_subscribers
from bot.core.utils import process_status_update


@log_function("scheduler_job")
async def scheduler_job() -> None:
    applications = await ApplicationModel.find({}).to_list()
    scraper = Scraper()

    for application in applications:
        try:
            await process_status_update(application, scraper, notify_subscribers)
        except Exception as e:
            # Log error but continue processing other applications
            from bot.core.logger import log_error

            log_error(
                f"Failed to process status update for session {application.session_id}",
                exception=e,
            )
