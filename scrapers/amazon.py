"""Amazon India scraper."""
from urllib.parse import quote_plus
from . import browser_page, parse_price, empty_result, first_price_in_page

SOURCE = "Amazon India"


async def scrape(query: str) -> dict:
    url = f"https://www.amazon.in/s?k={quote_plus(query + ' gaming laptop')}"
    try:
        async with browser_page() as page:
            await page.goto(url, timeout=45000, wait_until="domcontentloaded")

            # Amazon sometimes shows a CAPTCHA / "continue shopping" interstitial.
            try:
                cont = page.locator('button:has-text("Continue shopping")').first
                if await cont.count():
                    await cont.click(timeout=2000)
                    await page.wait_for_load_state("domcontentloaded")
            except Exception:
                pass

            card = page.locator(
                'div[data-component-type="s-search-result"]:not([data-asin=""])'
            ).first
            try:
                await card.wait_for(timeout=12000)
            except Exception:
                card = None

            title = link = price_text = None

            if card:
                # Title
                for sel in ["h2 span", "h2 a span", "span.a-text-normal"]:
                    loc = card.locator(sel).first
                    if await loc.count():
                        try:
                            title = (await loc.inner_text(timeout=2000)).strip()
                            if title:
                                break
                        except Exception:
                            pass

                # Link
                link_el = card.locator("h2 a, a.a-link-normal.s-no-outline").first
                if await link_el.count():
                    href = await link_el.get_attribute("href")
                    if href:
                        link = f"https://www.amazon.in{href}" if href.startswith("/") else href

                # Price
                for sel in ["span.a-price > span.a-offscreen", "span.a-price-whole"]:
                    loc = card.locator(sel).first
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
