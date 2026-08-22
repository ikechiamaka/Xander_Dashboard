from playwright.sync_api import sync_playwright
import os

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto("https://skylab.cdph.ca.gov/ODdash/?tab=CTY")
    page.wait_for_timeout(3000)

    page.evaluate("""
        () => {
            const el = $('#county2')[0].selectize;
            el.setValue('Monterey');
        }
    """)

    page.wait_for_timeout(4000)  # increased - give Shiny more time to regenerate the report

    with page.expect_download(timeout=60000) as download_info:  # longer timeout too
        page.click("#report")
    download = download_info.value

    save_path = os.path.join(DATA_DIR, "cdph_overdose_monterey.xlsx")
    download.save_as(save_path)

    # sanity check: did we actually get a real file, and how big is it?
    size = os.path.getsize(save_path)
    print(f"Downloaded to {save_path}, size: {size} bytes")

    browser.close()