from playwright.sync_api import sync_playwright
import os

DATA_DIR = "data"
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
        page = browser.new_page()
        page.goto("https://skylab.cdph.ca.gov/ODdash/?tab=CTY")
        page.wait_for_timeout(3000)

        # select Monterey
        page.evaluate("""
            () => {
                const el = $('#county2')[0].selectize;
                el.setValue('Monterey');
            }
        """)
        page.wait_for_timeout(4000)

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