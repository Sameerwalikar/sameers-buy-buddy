"""Reliance Digital scraper."""
from urllib.parse import quote_plus
from . import browser_page, parse_price, empty_result, first_price_in_page

SOURCE = "Reliance Digital"


async def scrape(query: str) -> dict:
    url = f"https://www.reliancedigital.in/search?q={quote_plus(query + ' gaming laptop')}"
    try:
        async with browser_page() as page:
            await page.goto(url, timeout=45000, wait_until="domcontentloaded")

            # Reliance is a React SPA — wait for hydration.
            try:
                await page.wait_for_load_state("networkidle", timeout=8000)
            except Exception:
                pass

            link = title = price_text = None

            # Newer Reliance Digital markup uses <a class="..."> wrapping each product.
            link_el = page.locator('a[href*="/p/"]').first
            if await link_el.count():
                href = await link_el.get_attribute("href")
                if href:
                    link = f"https://www.reliancedigital.in{href}" if href.startswith("/") else href

            # Title fallbacks
            for sel in [
                "p.sp__name",
                "a.sp__name",
                "div[class*='ProductCard'] p",
                "a[href*='/p/']",
            ]:
                loc = page.locator(sel).first
                if await loc.count():
                    try:
                        title = (await loc.inner_text(timeout=2000)).strip().split("\n")[0]
                        if title:
                            break
                    except Exception:
                        pass

            # Price fallbacks
            for sel in [
                "span#offerPrice",
                "div[class*='price'] span",
                "span[class*='Price']",
            ]:
                loc = page.locator(sel).first
                if await loc.count():
                    try:
                        price_text = await loc.inner_text(timeout=2000)
                        if price_text and "₹" in price_text:
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
