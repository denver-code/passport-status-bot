# Standard library imports
import os
import secrets

# Third party imports
import cloudscraper
from fake_headers import Headers

# Local application imports
from bot.core.logger import log_error, log_function, log_info, log_warning
from bot.core.playwright import playwright_check


class Scraper:
    def __init__(self) -> None:
        self.scraper = cloudscraper.create_scraper()

    @log_function("check")
    def check(
        self,
        identifier: str,
        retrive_all: bool = False,
        fallback_to_playwright: bool = True,
    ) -> list[dict[str, str]] | None:
        log_info(
            f"Checking status for {identifier} with retrive_all={retrive_all} and fallback_to_playwright={fallback_to_playwright}"
        )

        try:
            target_url = f"https://passport.mfa.gov.ua/Home/CurrentSessionStatus?sessionId={identifier}&_={secrets.randbelow(10**13) + 10**12}"
            log_info(f"Target URL: {target_url}")

            headers = Headers().generate()
            log_info(f"Headers: {headers}")

            # Enforce timeouts to avoid indefinite hanging
            connect_timeout = int(os.getenv("HTTP_CONNECT_TIMEOUT", "10"))
            read_timeout = int(os.getenv("HTTP_READ_TIMEOUT", "20"))
            log_info(
                f"HTTP timeouts -> connect: {connect_timeout}s, read: {read_timeout}s"
            )

            r = self.scraper.get(
                target_url,
                headers=headers,
                timeout=(connect_timeout, read_timeout),
                allow_redirects=True,
            )

            # If the request is not successful, log the warning and return None
            r_status_code = r.status_code
            log_info(f"Response status code: {r_status_code}")
            if r_status_code != 200:
                log_warning(
                    f"Request to {target_url} with headers {headers} returned status code {r_status_code}"
                )
                log_warning(f"Response content: {r.content}")

                # Fallback to Playwright in case of non-200 status
                if fallback_to_playwright:
                    log_info(f"Fallback to Playwright for {identifier}")
                    return playwright_check(identifier, retrive_all=retrive_all)  # type: ignore[no-any-return]
                return None

            # If the request is successful, parse the response content
            r_content = r.content
            log_info(f"Response content: {r_content}")
            if r_content:
                raw_json = r.json()
                log_info(f"Raw JSON: {raw_json}")
                parsed_json = raw_json["StatusInfo"]
                log_info(f"Parsed JSON: {parsed_json}")

                status_list: list[dict[str, str]] = []
                for status in parsed_json:
                    status_list.append(
                        {
                            "status": status["StatusName"],
                            "date": status["StatusDateUF"],
                        }
                    )

                # If the user wants to retrieve all statuses, return the list
                if retrive_all:
                    log_info(f"Retrieving all statuses: {status_list}")
                    return status_list

                log_info(f"Retrieving last status: {status_list[-1]}")
                return [status_list[-1]]

            # Fallback to Playwright in case content is empty/malformed
            if fallback_to_playwright:
                log_info(f"Fallback to Playwright for {identifier}")
                return playwright_check(identifier, retrive_all=retrive_all)  # type: ignore[no-any-return]
            return None
        except Exception as e:
            log_warning(
                f"Cloudscraper failed for {identifier}, trying Playwright. Error: {e}"
            )
            try:
                if fallback_to_playwright:
                    log_info(f"Fallback to Playwright for {identifier}")
                    return playwright_check(identifier, retrive_all=retrive_all)  # type: ignore[no-any-return]
                return None
            except Exception as e2:
                log_error(
                    f"Error checking status for {identifier} via Playwright: {e2}"
                )
                return None
