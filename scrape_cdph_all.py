from playwright.sync_api import sync_playwright
import os
from pathlib import Path

DATA_DIR = str(Path(__file__).resolve().parent / "data")
os.makedirs(DATA_DIR, exist_ok=True)

# all four values confirmed by inspecting the actual radio buttons on the page
DATA_SOURCES = {
    "deaths": "death",
    "ed_visits": "ed",
    "hospitalizations": "hsp",
    "prescriptions": "crs",
}


def scrape_cdph_chart(source_key, output_filename):
    radio_value = DATA_SOURCES[source_key]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/130 Safari/537.36")
        page.goto("https://skylab.cdph.ca.gov/ODdash/?tab=CTY", wait_until="domcontentloaded", timeout=90000)
        page.wait_for_timeout(5000)

        # select Monterey
        county_search = page.locator("#county2 + div input")
        county_search.fill("Monterey")
        page.locator(".selectize-dropdown .option", has_text="Monterey").click(timeout=30000)
        page.wait_for_timeout(5000)

        # find the download link and trace up to its tab panel (opens the panel,
        # which also makes the data-source radio buttons inside it clickable)
        page.wait_for_selector("#CTY-dlTime", state="attached", timeout=15000)
        panel_id = page.locator("#CTY-dlTime").locator(
            "xpath=ancestor::div[contains(@class,'tab-pane')]"
        ).last.get_attribute("id")

        tab_selector = f'a[aria-controls="{panel_id}"]'
        page.wait_for_selector(tab_selector, timeout=15000)
        page.click(tab_selector)
        page.wait_for_timeout(1500)

        # select the requested data source radio button
        page.check(f'input[name="CTY-src_h"][value="{radio_value}"]')
        page.wait_for_timeout(2500)  # let Shiny regenerate the chart + download link for this source

        page.locator("#CTY-dlTime:not(.disabled)").wait_for(state="attached", timeout=60000)
        with page.expect_download(timeout=60000) as download_info:
            page.click("#CTY-dlTime")
        download = download_info.value

        save_path = os.path.join(DATA_DIR, output_filename)
        download.save_as(save_path)

        size = os.path.getsize(save_path)
        print(f"[{source_key}] Downloaded to {save_path}, size: {size} bytes")

        browser.close()


if __name__ == "__main__":
    scrape_cdph_chart("deaths", "cdph_deaths_timetrend.csv")
    scrape_cdph_chart("ed_visits", "cdph_ed_visits_timetrend.csv")
    scrape_cdph_chart("hospitalizations", "cdph_hospitalizations_timetrend.csv")
    scrape_cdph_chart("prescriptions", "cdph_prescriptions_timetrend.csv")
