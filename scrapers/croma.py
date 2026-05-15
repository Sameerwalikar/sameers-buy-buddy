"""Croma scraper."""
from urllib.parse import quote_plus
from . import browser_page, parse_price, empty_result, first_price_in_page

SOURCE = "Croma"


async def scrape(query: str) -> dict:
    url = f"https://www.croma.com/searchB?q={quote_plus(query + ' gaming laptop')}&text={quote_plus(query)}"
    try:
        async with browser_page() as page:
            await page.goto(url, timeout=45000, wait_until="domcontentloaded")

            # Croma is a heavy SPA — wait for product list to render.
            try:
                await page.wait_for_load_state("networkidle", timeout=10000)
            except Exception:
                pass

            link = title = price_text = None

            # Title (also drives the link)
            for sel in ["h3.product-title a", "a.product-title", "h3 a[href*='/p/']"]:
                loc = page.locator(sel).first
                if await loc.count():
                    try:
                        title = (await loc.inner_text(timeout=2000)).strip()
                        href = await loc.get_attribute("href")
                        if href:
                            link = f"https://www.croma.com{href}" if href.startswith("/") else href
                        if title:
                            break
                    except Exception:
                        pass

            # Price
            for sel in [
                "span.amount",
                "span.new-price",
                "span[data-testid='new-price']",
                "div[class*='Price'] span",
            ]:
                loc = page.locator(sel).first
                if await loc.count():
                    try:
                        price_text = await loc.inner_text(timeout=2000)
                        if price_text and any(c.isdigit() for c in price_text):
                            break
                        price_text = None
                    except Exception:
                        pass

            if not price_text:
                price_text = await first_price_in_page(page)

            price = parse_price(price_text)
            return {
                "source": SOURCE,
                "title": title,
                "price": price,
                "link": link or url,
                "available": price is not None,
                "error": None if price else "no price found",
            }
    except Exception as e:
        return empty_result(SOURCE, str(e))
