import asyncio
import json as _json
import random
from contextlib import suppress
from typing import cast

import aiohttp

# Third party imports
from playwright.async_api import async_playwright

# Local application imports
from bot.core.logger import log_function, log_info, log_warning


@log_function("get_public_proxies_list")
async def _get_public_proxies_list(
    protocol: str = "http",
    country: str = "ua",
    proxy_format: str = "protocolipport",
    format_type: str = "text",
    anonymity: str = "Elite",
    proxies_limit: int = 10000,
    proxy_latency: float = 200,
) -> list[str]:
    """
    Fetch limited number of public HTTP proxies from multiple sources.
    Returns list of proxy URLs (limited to reduce connection attempts).

    Args:
        protocol: Protocol of proxies to return.
            - "http": HTTP (default)
            - "socks4": SOCKS4
            - "socks5": SOCKS5
            - "http,socks4,socks5": All protocols
        country: Country of proxies to return.
            - "ua": Ukraine (default)
            - "pl": Poland
            - "de": Germany
            - "fr": France
            - "it": Italy
            - "es": Spain
            - "nl": Netherlands
            - "be": Belgium
            - "ua,pl,de,es": several countries
        proxy_format: Format of proxy URLs to return.
            - "protocolipport": http://ip:port (default)
            - "ipport": ip:port
        format_type: Format of proxy URLs to return.
            - "text": text/plain (default)
            - "json": application/json
            - "csv": text/csv
        anonymity: Anonymity level of proxies to return.
            - "Elite": Elite (default)
            - "Anonymous": Anonymous
            - "Transparent": Transparent
            - "Elite,Anonymous,Transparent": All anonymity levels
        proxies_limit: Maximum number of proxies to return.
        proxy_latency: Latency of proxy connection in milliseconds.
    """
    sources = [
        f"https://api.proxyscrape.com/v4/free-proxy-list/get?request=get_proxies&country={country}&protocol={protocol}&skip=0&proxy_format={proxy_format}&format={format_type}&anonymity={anonymity}&timeout={proxy_latency}",
    ]

    public_proxies: list[str] = []

    async def fetch_text(url: str) -> str:
        try:
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, headers={"Accept": "text/plain"}) as resp:
                    if resp.status == 200:
                        text = await resp.text()
                        return str(text)
        except Exception:
            return ""
        return ""

    for url in sources:
        text = await fetch_text(url)
        if not text:
            continue
        for line in text.splitlines():
            candidate = line.strip()
            if not candidate:
                continue
            # Expect host:port or protocol://host:port
            if ":" not in candidate:
                continue
            if (
                candidate.startswith("http://")
                or candidate.startswith("https://")
                or candidate.startswith("socks4://")
                or candidate.startswith("socks5://")
            ):
                public_proxies.append(candidate)
            else:
                public_proxies.append(f"http://{candidate}")

    # Shuffle and limit to reasonable number
    random.shuffle(public_proxies)

    log_info(f"Found {len(public_proxies)} public proxies from {len(sources)} sources")

    # Return limited number of proxies
    return public_proxies[:proxies_limit]


@log_function("quick_check_proxy")
async def _quick_check_proxy(
    proxy_urls: list[str], timeout_sec: float = 30, max_concurrency: int = 20
) -> list[str]:
    log_info(
        f"Quick checking {len(proxy_urls)} proxies with timeout {timeout_sec}s, concurrency={max_concurrency}"
    )
    test_url = "https://httpbin.org/ip"
    alive_proxies: list[str] = []
    sem = asyncio.Semaphore(max_concurrency)

    async def check_proxy(proxy_url: str) -> None:
        async with sem:  # Limit concurrency
            with suppress(Exception):  # Ignore all connection errors
                async with aiohttp.ClientSession() as session:
                    timeout = aiohttp.ClientTimeout(total=timeout_sec)
                    async with session.get(
                        test_url, proxy=proxy_url, timeout=timeout
                    ) as resp:
                        if resp.status == 200:
                            alive_proxies.append(proxy_url)

    await asyncio.gather(*(check_proxy(proxy) for proxy in proxy_urls))

    log_info(f"Found {len(alive_proxies)} alive proxies from {len(proxy_urls)} tested")
    return alive_proxies


@log_function("test_proxy_connection")
async def _test_proxy_connection(
    proxy_urls: list[str], timeout_sec: float = 300, concurrency: int = 10
) -> list[str]:
    """
    Asynchronously test a list of proxies with one browser instance.
    concurrency — number of concurrent checks.
    """
    log_info(
        f"Testing {len(proxy_urls)} proxies with timeout {timeout_sec}s, concurrency={concurrency}"
    )
    test_url = "https://httpbin.org/ip"
    working_proxies: list[str] = []
    sem = asyncio.Semaphore(concurrency)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        async def test_proxy(proxy_url: str) -> bool:
            async with sem:
                context = None
                page = None
                try:
                    context = await browser.new_context(
                        proxy={"server": proxy_url}, ignore_https_errors=True
                    )
                    page = await context.new_page()

                    response = await page.goto(
                        test_url,
                        timeout=timeout_sec * 1000,  # ms
                        wait_until="domcontentloaded",
                    )

                    if response and response.status == 200:
                        try:
                            raw_text = await page.text_content("body")
                            if raw_text:
                                ip_data = _json.loads(raw_text)
                                ip_address = ip_data.get("origin")
                                if ip_address:
                                    log_info(
                                        f"✅ Proxy works: {proxy_url}, IP: {ip_address}"
                                    )
                                    return True
                                else:
                                    log_warning(
                                        f"⚠️ No IP in response from: {proxy_url}"
                                    )
                            else:
                                log_warning(f"⚠️ Empty response from: {proxy_url}")
                        except Exception as e:
                            log_warning(
                                f"⚠️ Failed to parse JSON from proxy {proxy_url}: {e}"
                            )
                    else:
                        status = response.status if response else "no response"
                        log_warning(
                            f"❌ Proxy failed with status {status}: {proxy_url}"
                        )

                except Exception as e:
                    log_warning(f"❌ Proxy error [{proxy_url}]: {e}")

                finally:
                    if page and not page.is_closed():
                        await page.close(run_before_unload=False)
                    if context:
                        await context.close()
                return False

        results = await asyncio.gather(
            *(test_proxy(proxy) for proxy in proxy_urls), return_exceptions=True
        )

        for proxy, result in zip(proxy_urls, results, strict=False):
            if isinstance(result, Exception):
                log_warning(f"⚠️ Proxy test crashed [{proxy}]: {result}")
            elif result:
                working_proxies.append(proxy)

        await browser.close()

    log_info(
        f"Found {len(working_proxies)} working proxies from {len(proxy_urls)} tested"
    )
    return working_proxies


@log_function("get_working_proxies")
async def get_working_proxies() -> list[str]:
    """
    Get working proxies from the internet.
    """
    available_proxies = await _get_public_proxies_list(
        country="ua,pl,de,es,ro,lt,sk", protocol="http,socks4,socks5"
    )

    alive_proxies = await _quick_check_proxy(available_proxies)

    working_proxies = cast(list[str], await _test_proxy_connection(alive_proxies))

    log_info(
        f"Available proxies: {len(available_proxies)} | Alive proxies: {len(alive_proxies)} | Working proxies: {len(working_proxies)}"
    )

    return working_proxies
