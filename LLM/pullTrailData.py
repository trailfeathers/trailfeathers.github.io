import requests
import time
import csv
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

base_url = "https://www.wta.org/go-outside/hikes"

# Your original search parameters
params = {
    "title": "",
    "region": "all",
    "report_recency": "anytime",
    "min_rating": "0",
    "show_incomplete": "on",
    "mileage:list:float": "0.0",
    "mileage:list:float": "25",
    "elevation_gain:list:int": "0",
    "elevation_gain:list:int": "5000",
    "highpoint": "",
    "searchabletext": "",
    "sort_on": "rating",
    "filter": "Search"
}

offset = 0

links = []

while offset <= 120:

    # Add pagination offset
    params["b_start:int"] = offset

    #print(f"\nScraping results starting at {offset}")

    r = requests.get(base_url, params=params)
    soup = BeautifulSoup(r.text, "html.parser")

    # Find listing container
    listing = soup.find("div", id="search-result-listing")

    if listing is None:
        #print("Listing not found — stopping.")
        break

    # Find all hike result items
    items = listing.find_all("div", class_="search-result-item")

    if not items:
        #print("No more hikes — finished.")
        break

    #print("Items on page:", len(items))

    # Extract links
    for item in items:
        link = item.find("a")
        if link:
            title = link.text.strip()
            href = link.get("href")
            #print(title, "→", href)
            links.append(href)

    # Move to next page
    offset += 30

    time.sleep(1)

print(links)

all_hikes = []

# --- Selenium setup ---
options = Options()
options.headless = True  # run browser in background
driver = webdriver.Chrome(options=options)

for url in links:
    print("\n===============================")
    print("Scraping URL:", url)
    driver.get(url)

    # Scroll down to bottom to trigger lazy-loading trip reports
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(3)  # wait for trip reports to load

    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")

    # --- Title ---
    title_el = soup.find("h1")
    title = title_el.get_text(strip=True) if title_el else "0"
    print("Title found:", title)

    # --- Full description ---
    desc_div = soup.find("div", id="hike-full-description")
    description = desc_div.get_text(" ", strip=True) if desc_div else "0"
    print("Description snippet:", description[:100], "..." if len(description) > 100 else "")

    # --- Stats ---
    stats_divs = soup.find_all(
        "div",
        class_=["hike-stats__stat", "hike-stats__stat--last-row"]
    )
    stats_data = {}
    print("Number of stats divs found:", len(stats_divs))
    for div in stats_divs:
        dt_el = div.find("dt")
        dt = dt_el.get_text(strip=True) if dt_el else "Unknown"
        dds = [dd.get_text(strip=True) for dd in div.find_all("dd")]
        print(f"Stat '{dt}' with values: {dds}")
        for i, val in enumerate(dds, 1):
            stats_data[f"{dt}_{i}"] = val if val else "0"

    # --- WTA headline spans ---
    headline_spans = soup.find_all("span", class_="wta-icon-headline__text")
    headline_data = {}
    print("Number of headline spans found:", len(headline_spans))
    for span in headline_spans:
        label_span = span.find("span", class_="h4")
        if label_span:
            label = label_span.get_text(strip=True).rstrip(":")
            value = span.get_text(" ", strip=True).replace(label_span.get_text(strip=True), "").strip()
            headline_data[label] = value if value else "0"
            print(f"Headline '{label}' -> '{value}'")

    # --- Trip reports ---
    trip_reports_div = soup.find("div", id="trip-reports")
    trip_titles = []
    trip_texts = []

    if trip_reports_div:
        reports = trip_reports_div.find_all("div", class_="item")[:2]
        print("Number of trip reports found:", len(reports))

        for idx, report in enumerate(reports, start=1):
            # Title link
            a_tag = report.find("h3", class_="listitem-title").find("a")
            report_title = a_tag.get_text(strip=True) if a_tag else "0"
            report_url = a_tag.get("href") if a_tag else "0"
            trip_titles.append(f"{report_title} ({report_url})")

            # Full text paragraphs
            full_text_div = report.find("div", class_="report-text show-excerpt")
            if full_text_div:
                text_container = full_text_div.find("div", class_="trip-report-full-text")
                if text_container:
                    paragraphs = [p.get_text(" ", strip=True) for p in text_container.find_all("p")]
                    full_text = " ".join(paragraphs) if paragraphs else "0"
                else:
                    full_text = "0"
            else:
                full_text = "0"
            trip_texts.append(full_text)

            print(f"Trip Report {idx} Title: {report_title}")
            print(f"Trip Report {idx} Text snippet: {full_text[:100]}{'...' if len(full_text)>100 else ''}")

    else:
        print("Trip reports container not found")
    
    # --- Combine everything ---
    hike_info = {
        "Hike Name": title,
        "Description": description,
        "Trip Report 1 Title": trip_titles[0] if len(trip_titles) > 0 else "0",
        "Trip Report 1 Text": trip_texts[0] if len(trip_texts) > 0 else "0",
        "Trip Report 2 Title": trip_titles[1] if len(trip_titles) > 1 else "0",
        "Trip Report 2 Text": trip_texts[1] if len(trip_texts) > 1 else "0",
        "URL": url
    }

    hike_info.update(stats_data)
    hike_info.update(headline_data)

    all_hikes.append(hike_info)
    time.sleep(1)  # polite delay between hikes

driver.quit()

# --- Write to CSV ---
if all_hikes:
    fieldnames = set()
    for hike in all_hikes:
        fieldnames.update(hike.keys())
    fieldnames = list(fieldnames)

    with open("test.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_hikes)

print("\nScraping complete. Saved to test.csv")


