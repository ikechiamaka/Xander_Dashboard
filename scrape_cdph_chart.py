from playwright.sync_api import sync_playwright
import os

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto("https://skylab.cdph.ca.gov/ODdash/?tab=CTY")
    page.wait_for_timeout(3000)

    # select Monterey - confirmed working
    page.evaluate("""
        () => {
            const el = $('#county2')[0].selectize;
            el.setValue('Monterey');
        }
    """)
    page.wait_for_timeout(4000)  # let Shiny regenerate the chart + download link for Monterey

    print("Looking for CTY-dlTime element...")
    page.wait_for_selector("#CTY-dlTime", state="attached", timeout=15000)
    print("Found it. Tracing up to parent tab-pane...")

    panel_id = page.locator("#CTY-dlTime").locator(
        "xpath=ancestor::div[contains(@class,'tab-pane')]"
    ).last.get_attribute("id")
    print(f"Parent panel id: {panel_id}")

    tab_selector = f'a[aria-controls="{panel_id}"]'
    print(f"Looking for tab with selector: {tab_selector}")
    page.wait_for_selector(tab_selector, timeout=15000)
    print("Found tab, clicking...")
    page.click(tab_selector)
    page.wait_for_timeout(2000)  # let Shiny render now that the tab is active

    page.screenshot(path="debug_before_download.png")
    print("Screenshot saved. Attempting download click...")

    with page.expect_download(timeout=60000) as download_info:
        page.click("#CTY-dlTime")
    download = download_info.value

    save_path = os.path.join(DATA_DIR, "cdph_opioid_deaths_timetrend.csv")
    download.save_as(save_path)

    size = os.path.getsize(save_path)
    print(f"Downloaded to {save_path}, size: {size} bytes")

    browser.close()