"""Flipkart scraper."""
from urllib.parse import quote_plus
from . import browser_page, parse_price, empty_result, first_price_in_page

SOURCE = "Flipkart"


async def scrape(query: str) -> dict:
    url = f"https://www.flipkart.com/search?q={quote_plus(query + ' gaming laptop')}"
    try:
        async with browser_page() as page:
            await page.goto(url, timeout=45000, wait_until="domcontentloaded")

            # Dismiss the login modal that pops up on every cold visit.
            for sel in ['button:has-text("✕")', 'button._2KpZ6l._2doB4z']:
                try:
                    btn = page.locator(sel).first
                    if await btn.count():
                        await btn.click(timeout=1500)
                        break
                except Exception:
                    pass

            # Wait until at least one product card is in the DOM.
            try:
                await page.locator('a[href*="/p/"]').first.wait_for(timeout=12000)
            except Exception:
                pass

            link = title = price_text = None

            link_el = page.locator('a[href*="/p/"]').first
            if await link_el.count():
                href = await link_el.get_attribute("href")
                if href:
                    link = f"https://www.flipkart.com{href}" if href.startswith("/") else href

            # Title — Flipkart rotates classes; try several + fall back to img alt.
            for sel in [
                "div.KzDlHZ",         # current laptop card title
                "div._4rR01T",        # older title class
                "a.wjcEIp",           # newer link-as-title
                "a.IRpwTa",           # mobile/alt layout
                "a[href*='/p/'] img", # image alt as last resort
            ]:
                loc = page.locator(sel).first
                if await loc.count():
                    try:
                        if "img" in sel:
                            title = await loc.get_attribute("alt")
                        else:
                            title = (await loc.inner_text(timeout=2000)).strip()
                        if title:
                            break
                    except Exception:
                        pass

            # Price
            for sel in ["div.Nx9bqj", "div._30jeq3", "div._30jeq3._1_WHN1"]:
                loc = page.locator(sel).first
                if await loc.count():
                    try:
                        price_text = await loc.inner_text(timeout=2000)
                        if price_text:
                            break
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
