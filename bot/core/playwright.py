"""Playwright-based fallback fetcher."""

# Standard library imports
import asyncio
import json as _json
import os
import secrets
import shutil
import tempfile
from concurrent.futures import ThreadPoolExecutor
from typing import Any

# Third party imports
from playwright.async_api import async_playwright

# Local application imports
from bot.core.logger import log_error, log_function, log_info, log_warning
from bot.core.proxy import get_working_proxies


@log_function("apply_stealth_to_context")
async def _apply_stealth_to_context(context: Any) -> None:
    """
    Apply basic stealth measures to defeat simple bot detection:
    - navigator.webdriver
    - plugins/languages/platform
    - WebGL vendor/renderer
    """
    await context.add_init_script(
        """
        Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        // Languages
        Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
        // Plugins length
        Object.defineProperty(navigator, 'plugins', { get: () => [1,2,3,4,5] });
        // Platform
        Object.defineProperty(navigator, 'platform', { get: () => 'MacIntel' });
        // WebGL vendor/renderer spoofing
        const getParameter = WebGLRenderingContext.prototype.getParameter;
        WebGLRenderingContext.prototype.getParameter = function(parameter) {
          // UNMASKED_VENDOR_WEBGL
          if (parameter === 37445) { return 'Apple Inc.'; }
          // UNMASKED_RENDERER_WEBGL
          if (parameter === 37446) { return 'Apple M1'; }
          return getParameter.call(this, parameter);
        };
        // chrome.runtime spoof
        window.chrome = { runtime: {} };
        // hairline fix
        Object.defineProperty(window, 'devicePixelRatio', { get: () => 2 });
        // Permissions query spoof
        const originalQuery = window.navigator.permissions && window.navigator.permissions.query;
        if (originalQuery) {
          window.navigator.permissions.query = (parameters) => (
            parameters && parameters.name === 'notifications'
              ? Promise.resolve({ state: Notification.permission })
              : originalQuery(parameters)
          );
        }
        """
    )


@log_function("playwright_check_async")
async def _playwright_check_async(
    identifier: str, retrive_all: bool = False
) -> list | None:
    """
    Enhanced Playwright check with better Cloudflare handling and timeout management.
    """
    base_target_url = (
        f"https://passport.mfa.gov.ua/Home/CurrentSessionStatus?sessionId={identifier}"
    )

    # Configuration
    TARGET_TIMEOUT = (
        int(os.getenv("PLAYWRIGHT_TARGET_TIMEOUT", "15")) * 1000
    )  # Convert to ms

    async with async_playwright() as p:
        raw_json = None
        browser = None
        context = None
        page = None
        video_tmpdir = None

        # Helper to execute a series of attempts with given proxies list
        async def _run_attempts(attempts_list: list[str | None]) -> bool:
            nonlocal raw_json, browser, context, page, video_tmpdir
            for attempt_num, proxy_url in enumerate(attempts_list, 1):
                proxy_options = {"server": proxy_url} if proxy_url else None
                log_info(
                    f"Attempt {attempt_num}/{len(attempts_list)}: {'Using proxy ' + str(proxy_url) if proxy_url else 'Direct connection'}"
                )

                try:
                    # Launch browser with shorter timeouts
                    # Ensure proxy is typed correctly for Playwright
                    from playwright.async_api import ProxySettings

                    typed_proxy: ProxySettings | None
                    if proxy_options:
                        # Build ProxySettings explicitly to avoid ** expansion of dict
                        typed_proxy = ProxySettings(server=str(proxy_options["server"]))
                    else:
                        typed_proxy = None

                    browser = await p.chromium.launch(
                        headless=True,
                        proxy=typed_proxy,
                        args=[
                            "--disable-blink-features=AutomationControlled",
                            "--no-sandbox",
                            "--disable-dev-shm-usage",
                            "--disable-web-security",
                            "--disable-features=VizDisplayCompositor",
                            "--disable-backgrounding-occluded-windows",
                        ],
                    )

                    # Setup video recording from the beginning
                    video_tmpdir = tempfile.mkdtemp(prefix="pwvideo_")
                    context = await browser.new_context(
                        user_agent=(
                            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                            "AppleWebKit/537.36 (KHTML, like Gecko) "
                            "Chrome/125.0.0.0 Safari/537.36"
                        ),
                        viewport={"width": 1280, "height": 800},
                        locale="en-US",
                        timezone_id="Europe/Kiev",
                        record_video_dir=video_tmpdir,
                        record_video_size={"width": 1280, "height": 720},
                        ignore_https_errors=True,  # Handle SSL issues
                    )

                    await _apply_stealth_to_context(context)
                    page = await context.new_page()

                    # Set headers for better compatibility
                    await page.set_extra_http_headers(
                        {
                            "Accept": "application/json, text/javascript, */*; q=0.01",
                            "Accept-Language": "en-US,en;q=0.9",
                            "Cache-Control": "no-cache",
                            "Pragma": "no-cache",
                            "Referer": "https://passport.mfa.gov.ua/",
                            "Sec-Fetch-Dest": "empty",
                            "Sec-Fetch-Mode": "cors",
                            "Sec-Fetch-Site": "same-origin",
                        }
                    )

                    # Enhanced Cloudflare challenge handling
                    try:
                        # Add random parameter to bypass Cloudflare cache
                        target_url_with_nonce = (
                            f"{base_target_url}&_={secrets.randbelow(10**13) + 10**12}"
                        )

                        # Navigate to target URL with recording from start
                        resp = await page.goto(
                            target_url_with_nonce,
                            wait_until="domcontentloaded",
                            timeout=TARGET_TIMEOUT,
                        )

                        # Check for Cloudflare challenges or blocks
                        page_content = await page.content()
                        page_title = await page.title()
                        page_url = page.url

                        # Detect various Cloudflare scenarios
                        is_challenge = any(
                            [
                                "challenges.cloudflare.com" in page_url,
                                "Just a moment" in page_title,
                                "cf-browser-verification" in page_content,
                                "cf-chl-" in page_content,
                                "cf-captcha-container" in page_content,
                                resp and resp.status in [403, 503, 429],
                            ]
                        )

                        if is_challenge:
                            status_code = resp.status if resp else "unknown"
                            log_info(
                                f"Cloudflare challenge detected. Title: {page_title}, Status: {status_code}"
                            )

                            # Handle different challenge types
                            if "challenges.cloudflare.com" in page_url:
                                log_warning(
                                    "Blocked by challenges.cloudflare.com - trying to proceed"
                                )
                                # Wait for potential auto-solve
                                try:
                                    await page.wait_for_url(
                                        lambda url: "challenges.cloudflare.com"
                                        not in url,
                                        timeout=20000,
                                    )
                                    # Reload target page after challenge
                                    resp = await page.goto(
                                        target_url_with_nonce,
                                        wait_until="domcontentloaded",
                                        timeout=TARGET_TIMEOUT,
                                    )
                                except Exception:
                                    log_warning(
                                        "Failed to bypass challenges.cloudflare.com"
                                    )
                                    await _make_screenshot_and_send_to_admin(
                                        page, base_target_url, identifier
                                    )
                                    continue
                            else:
                                # Wait for cf_clearance cookie
                                log_info(
                                    "Waiting for Cloudflare challenge to complete..."
                                )
                                for _wait_sec in range(25):  # Wait up to 25 seconds
                                    await asyncio.sleep(1)
                                    cookies = await context.cookies()
                                    if any(
                                        c.get("name") == "cf_clearance" for c in cookies
                                    ):
                                        log_info("cf_clearance cookie obtained")
                                        break
                                    # Check if page changed
                                    current_url = page.url
                                    if "challenges.cloudflare.com" not in current_url:
                                        break

                                # Reload after potential clearance
                                try:
                                    resp = await page.goto(
                                        target_url_with_nonce,
                                        wait_until="domcontentloaded",
                                        timeout=TARGET_TIMEOUT,
                                    )
                                except Exception:
                                    log_warning(
                                        "Failed to reload after Cloudflare challenge"
                                    )
                                    await _make_screenshot_and_send_to_admin(
                                        page, base_target_url, identifier
                                    )
                                    continue

                        # Try to fetch JSON data
                        try:
                            raw_json = await page.evaluate(
                                "async (url) => { \n"
                                "  const r = await fetch(url, { credentials: 'include' }); \n"
                                "  if (!r.ok) throw new Error('Bad status: ' + r.status); \n"
                                "  return await r.json(); \n"
                                "}",
                                target_url_with_nonce,
                            )
                            log_info("Successfully fetched JSON data")
                            return True  # Success!

                        except Exception as fetch_err:
                            log_warning(f"Failed to fetch JSON: {fetch_err}")
                            await _make_screenshot_and_send_to_admin(
                                page, base_target_url, identifier
                            )
                            # Fallback to response parsing
                            if resp and resp.status == 200:
                                try:
                                    raw_text = await resp.text()
                                    raw_json = _json.loads(raw_text)
                                    return True
                                except Exception:
                                    try:
                                        text = await page.evaluate(
                                            "() => document.body.innerText"
                                        )
                                        raw_json = _json.loads(text)
                                        return True
                                    except Exception as e:
                                        log_warning(
                                            f"Error parsing JSON from page innerText: {e}"
                                        )
                                        pass

                        # If this is the last attempt, capture error info
                        if attempt_num == len(attempts_list):
                            await _send_error_to_admin(
                                page, base_target_url, identifier, None, video_tmpdir
                            )

                    except Exception as e:
                        log_warning(f"Error during Cloudflare challenge handling: {e}")
                        if attempt_num == len(attempts_list):
                            await _send_error_to_admin(
                                page, base_target_url, identifier, None, video_tmpdir
                            )
                        continue

                except Exception as e:
                    log_warning(f"Error launching browser or handling Playwright: {e}")
                    continue

                finally:
                    # Cleanup current attempt
                    if context:
                        try:
                            await context.close()
                        except Exception as e:
                            log_warning(f"Error closing context: {e}")
                    if browser:
                        try:
                            await browser.close()
                        except Exception as e:
                            log_warning(f"Error closing browser: {e}")
                    if video_tmpdir:
                        try:
                            shutil.rmtree(video_tmpdir, ignore_errors=True)
                        except Exception as e:
                            log_warning(f"Error removing video_tmpdir: {e}")

            return False

        # Phase 1: Try direct connection first
        direct_success = await _run_attempts([None])

        # Phase 2: Optionally try proxies if enabled and direct failed
        use_proxies = os.getenv("PLAYWRIGHT_ENABLE_PROXIES", "0") == "1"
        if not direct_success and use_proxies:
            try:
                working_proxies = await get_working_proxies()
            except Exception as e:
                log_warning(f"Failed to get working proxies: {e}")
                working_proxies = []

            if working_proxies:
                await _run_attempts(working_proxies)

        # Clean up successful video recording
        if raw_json and video_tmpdir:
            try:
                shutil.rmtree(video_tmpdir, ignore_errors=True)
            except Exception as e:
                log_warning(f"Error removing video_tmpdir at end: {e}")

    if not raw_json or "StatusInfo" not in raw_json:
        log_warning(f"No valid data retrieved for identifier {identifier}")
        return None

    parsed_json = raw_json["StatusInfo"]
    status_list = [
        {"status": status.get("StatusName"), "date": status.get("StatusDateUF")}
        for status in parsed_json
    ]

    if retrive_all:
        return status_list
    return [status_list[-1]] if status_list else None


@log_function("make_screenshot_and_send_to_admin")
async def _make_screenshot_and_send_to_admin(
    page: Any, target_url: str, identifier: str
) -> None:
    """
    Make screenshot and send to admin for debugging.
    """
    try:
        screenshot_bytes = await page.screenshot(full_page=True)
        with open("screenshot.png", "wb") as f:
            f.write(screenshot_bytes)
        await _send_error_to_admin(page, target_url, identifier, screenshot_bytes, None)
        # Remove screenshot
        os.remove("screenshot.png")
    except Exception as screenshot_err:
        log_warning(f"Failed to make screenshot: {screenshot_err}")


@log_function("send_error_to_admin")
async def _send_error_to_admin(
    page: Any,
    target_url: str,
    identifier: str,
    screenshot_bytes: bytes | None,
    video_tmpdir: str | None,
) -> None:
    """Send error screenshot and video to admin for debugging."""
    try:
        from aiogram import Bot

        from bot.core.config import settings

        token = getattr(settings, "TOKEN", None)
        admin_id = getattr(settings, "ADMIN_ID", None)
        if not token or not admin_id:
            return

        bot_tmp = Bot(token=token)

        # Capture screenshot
        try:
            # Try to click reveal button for IP info
            btn = await page.query_selector("#cf-footer-ip-reveal")
            if btn:
                await btn.click()
                await asyncio.sleep(1)

            # Use provided screenshot_bytes or capture new one
            if screenshot_bytes is None:
                screenshot_bytes = await page.screenshot(full_page=True)

            from aiogram.types import BufferedInputFile

            photo_file = BufferedInputFile(screenshot_bytes, filename="screenshot.png")
            await bot_tmp.send_photo(
                chat_id=admin_id,
                photo=photo_file,
                caption=f"🚨 Playwright failed for {identifier}\nURL: {target_url}\nTitle: {await page.title()}",
            )
        except Exception as screenshot_err:
            log_warning(f"Failed to send screenshot: {screenshot_err}")

        # Send video if available
        try:
            if video_tmpdir and os.path.exists(video_tmpdir):
                # Find video file in temp directory
                video_files = [
                    f for f in os.listdir(video_tmpdir) if f.endswith(".webm")
                ]
                if video_files:
                    video_path = os.path.join(video_tmpdir, video_files[0])
                    with open(video_path, "rb") as vf:
                        video_bytes = vf.read()
                    from aiogram.types import BufferedInputFile

                    video_file = BufferedInputFile(
                        video_bytes, filename="recording.webm"
                    )
                    await bot_tmp.send_video(
                        chat_id=admin_id,
                        video=video_file,
                        caption="📹 Session recording",
                    )
        except Exception as video_err:
            log_warning(f"Failed to send video: {video_err}")

        # Close bot session
        await bot_tmp.session.close()

    except Exception as notify_err:
        log_warning(f"Failed to notify admin: {notify_err}")


@log_function("playwright_check")
def playwright_check(identifier: str, retrive_all: bool = False) -> list | None:
    """
    Run the async Playwright flow in a background thread to avoid the
    "Sync API inside asyncio loop" issue and keep a sync interface.
    """
    try:
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(
                lambda: asyncio.run(_playwright_check_async(identifier, retrive_all))
            )
            return future.result()  # type: ignore[no-any-return]
    except Exception as e:
        log_error(f"Playwright check failed for {identifier}", exception=e)
        return None
