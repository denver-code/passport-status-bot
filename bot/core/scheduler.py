from datetime import datetime
from bot.core.api import Scraper
from bot.core.models.application import ApplicationModel, StatusModel
from bot.core.notificator import notify_subscribers


async def scheduler_job():
    _applications = await ApplicationModel.find({}).to_list()

    scraper = Scraper()
    for application in _applications:
        status = scraper.check(application.session_id, retrive_all=True)

        if not status:
            continue

        _statuses = []
        for s in status:
            _statuses.append(
                StatusModel(
                    status=s.get("status"),
                    date=s.get("date"),
                )
            )
        if len(_statuses) > len(application.statuses):
            # find new statuses
            new_statuses = _statuses[len(application.statuses) :]
            # notify subscribers
            await notify_subscribers(
                target_application=application, new_statuses=new_statuses
            )

        application.statuses = _statuses
        application.last_update = datetime.now()

        await application.save()
