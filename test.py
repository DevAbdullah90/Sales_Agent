import csv
import time
import re
import requests
from apify_client import ApifyClient
import re
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

# --------- Config ----------
API_TOKEN = "apify_api_45bXPtSZEeycjA30BR4oMHVNOELZP308tjTt"
ACTOR_ID = "compass/crawler-google-places"  # Apify Actor ID

client = ApifyClient(token=API_TOKEN)

# ---------- Email extraction ----------
def extract_emails_fast(base_url):
    likely_pages = [
        "/", "/about", "/contact"
    ]
    found_emails = set()
    domain = urlparse(base_url).netloc

    email_regex = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        for path in likely_pages:
            url = urljoin(base_url, path)
            try:
                print("Scanning:", url)
                page.goto(url, timeout=15000)
                page.wait_for_load_state("networkidle")
                html = page.content()
                emails = re.findall(email_regex, html)
                if emails:
                    found_emails.update(emails)
            except:
                continue

        browser.close()
    return list(found_emails)


# ---------- Run Actor ----------
def run_actor(location, keyword, max_items=50):
    actor_input = {
        "searchStringsArray": [f"{keyword} in {location}"],  # Required by Actor
        "maxCrawledPlacesPerSearch": max_items,  # Correct field according to latest doc
        "language": "en",
        "proxy": {"useApifyProxy": True},
    }

    # Start Actor
    run = client.actor(ACTOR_ID).call(run_input=actor_input)
    run_id = run["id"]
    dataset_id = run["defaultDatasetId"]
    print(f"Actor run started. Run ID: {run_id}, Dataset ID: {dataset_id}")

    # Wait until run finishes
    status = run["status"]
    while status not in ("SUCCEEDED", "FAILED", "ABORTED"):
        time.sleep(5)
        run = client.run(run_id).get()
        status = run["status"]
        print("Current status:", status)

    if status != "SUCCEEDED":
        raise Exception(f"Actor run failed, status = {status}")

    # Fetch items and limit to max_items manually if needed
    items = client.dataset(dataset_id).list_items().items
    return items

# ---------- Save CSV ----------
def save_to_csv(items, csv_filename="leads4.csv"):
    fieldnames = ["name", "url", "phone", "email", "address", "placeId"]

    with open(csv_filename, mode="w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for item in items:
            website = item.get("website")  # USE website field from Actor
            email = extract_emails_fast(website) if website else ""
            writer.writerow({
                "name": item.get("title") or item.get("name"),
                "url": website or item.get("url"),  # fallback to Google Maps URL
                "phone": item.get("phone"),
                "email": email,
                "address": item.get("address"),
                "placeId": item.get("placeId"),
            })
    print(f"Saved {len(items)} items to {csv_filename}")

# ---------- Main ----------
def main():
    location = input("Enter location (city, state or country): ")
    keyword = input("Enter business type or keyword (e.g., cafe, restaurant): ")
    max_items = int(input("Maximum number of results to fetch: "))

    items = run_actor(location, keyword, max_items)
    save_to_csv(items)

if __name__ == "__main__":
    main()
