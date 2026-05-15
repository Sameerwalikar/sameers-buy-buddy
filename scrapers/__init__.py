"""Shared Playwright helpers for all scrapers."""
import re
from contextlib import asynccontextmanager
from playwright.async_api import async_playwright

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/125.0.0.0 Safari/537.36"
)

# Minimal stealth: hide navigator.webdriver and a couple of other tells.
STEALTH_JS = """
Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
Object.defineProperty(navigator, 'languages', { get: () => ['en-IN', 'en-US', 'en'] });
Object.defineProperty(navigator, 'plugins',   { get: () => [1, 2, 3, 4, 5] });
window.chrome = { runtime: {} };
"""

EXTRA_HEADERS = {
    "Accept-Language": "en-IN,en-US;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Upgrade-Insecure-Requests": "1",
}

# Block heavyweight assets to speed up page loads (we only need HTML + a bit of JS).
BLOCKED_RESOURCES = {"image", "media", "font"}


@asynccontextmanager
async def browser_page(block_assets: bool = True):
    """Spin up a stealthy headless Chromium page tuned for Indian e-commerce sites."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ],
        )
        context = await browser.new_context(
            user_agent=USER_AGENT,
            locale="en-IN",
            timezone_id="Asia/Kolkata",
            viewport={"width": 1366, "height": 768},
            extra_http_headers=EXTRA_HEADERS,
        )
        await context.add_init_script(STEALTH_JS)

        if block_assets:
            async def _route(route):
                if route.request.resource_type in BLOCKED_RESOURCES:
                    await route.abort()
                else:
                    await route.continue_()
            await context.route("**/*", _route)

        page = await context.new_page()
        try:
            yield page
        finally:
            await context.close()
            await browser.close()


PRICE_RE = re.compile(r"₹\s?([\d,]{3,})")


def parse_price(text: str | None) -> float | None:
    """'₹1,29,990' -> 129990.0  (also tolerates plain numbers)."""
    if not text:
        return None
    m = PRICE_RE.search(text)
    raw = m.group(1) if m else text
    digits = re.sub(r"[^\d]", "", raw)
    try:
        return float(digits) if digits else None
    except ValueError:
        return None


async def first_price_in_page(page) -> str | None:
    """Last-resort: scrape the first ₹ price visible anywhere on the page."""
    try:
        body = await page.locator("body").inner_text(timeout=5000)
    except Exception:
        return None
    m = PRICE_RE.search(body or "")
    return f"₹{m.group(1)}" if m else None


def empty_result(source: str, error: str | None = None) -> dict:
    return {
        "source": source,
        "title": None,
        "price": None,
        "link": None,
        "available": False,
        "error": error,
    }
