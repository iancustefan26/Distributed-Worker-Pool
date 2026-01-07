from playwright.sync_api import sync_playwright
import json
import os

CFG_PATH = "src/cfg/crawler.json"

def get_semrush_countries():
    """
    Retrieve the list of available SEMrush countries using browser automation.

    This function launches a headless Chromium browser via Playwright, navigates
    to the SEMrush top websites page, opens the country selection dropdown, and
    extracts all available country options. Each country is returned as a
    dictionary containing its display name and associated value.

    :return: A list of dictionaries with country names and values.
    """

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True
        )

        page = browser.new_page()

        page.goto(
            "https://www.semrush.com/website/top/",
            wait_until="networkidle"
        )

        page.locator(
            'button[data-ui-name="Select.Trigger"][value="global"]'
        ).click()

        # Wait for dropdown
        page.wait_for_selector(
            'div[data-ui-name="Select.Popper"]',
            timeout=10000
        )

        #Extract countries
        options = page.locator(
            'div[data-ui-name="Select.Option"][role="option"]'
        )

        countries = []
        for i in range(options.count()):
            option = options.nth(i)
            countries.append({
                "name": option.inner_text().strip(),
                "value": option.get_attribute("value")
            })

        browser.close()
        return countries

def store_semrush_country_links():
    """
    Generate and store SEMrush country-specific URLs based on available countries.

    This function fetches the list of SEMrush-supported countries, loads the
    SEMrush configuration from the crawler configuration file, and constructs
    country-specific URLs using the configured base URL. All generated URLs are
    written to an output file, which is created if it does not already exist.

    :return: The filesystem path to the file containing the stored country URLs.
    """

    countries = get_semrush_countries()
    
    with open(CFG_PATH, "r") as f:
        config = json.load(f)["semrush_valid_countries"]

    base_url = config["base_url"]
    output_dir = config["output_dir"]
    output_file = config["output_file"]

    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, output_file)

    urls = []

    for country in countries:
        country_code = country.get("value")
        if not country_code:
            continue

        url = base_url.format(country=country_code)
        urls.append(url)

    with open(output_path, "w", encoding="utf-8") as f:
        for url in urls:
            f.write(url + "\n")

    return output_path

