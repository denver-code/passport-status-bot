import os

from fake_headers import Headers
import cloudscraper
from datetime import datetime


class Scraper:
    def __init__(self):
        self.scraper = cloudscraper.create_scraper()

    def check(self, identifier, retrive_all=False):
        try:
            headers = Headers().generate()

            r = self.scraper.get(
                f"http://passport.mfa.gov.ua/Home/CurrentSessionStatus?sessionId={identifier}",
                headers=headers,
            )

            if r.content:
                raw_json = r.json()
                parsed_json = raw_json["StatusInfo"]

                status_list = []
                for status in parsed_json:
                    status_list.append(
                        {
                            "status": status["StatusName"],
                            "date": status["StatusDateUF"],
                        }
                    )

                if retrive_all:
                    return status_list

                return [status_list[-1]]
            return None
        except Exception as e:
            return None
