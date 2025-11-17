from agents import function_tool
import requests
import re
import os
import time
from dotenv import load_dotenv
import uuid
from bs4 import BeautifulSoup
import csv
from apify_client import ApifyClient
from urllib.parse import urljoin, urlparse

load_dotenv()

# --------- Config ----------
API_TOKEN = os.getenv("APIFY_API_KEY")
ACTOR_ID = "compass/crawler-google-places"  # Apify Actor ID

client = ApifyClient(token=API_TOKEN)

# ---------- Email extraction ----------
from playwright.async_api import async_playwright

import re
from urllib.parse import urljoin
from playwright.async_api import async_playwright

async def extract_emails_fast_async(base_url):
    likely_pages = ["/", "/about", "/contact"]
    found_emails = set()
    email_regex = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"

    print(f"\n🔍 Starting email extraction for: {base_url}\n")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        for path in likely_pages:
            url = urljoin(base_url, path)
            print(f"➡️ Visiting: {url}")

            try:
                await page.goto(url, timeout=60000)
                print("   ✔ Page loaded")

                await page.wait_for_load_state("networkidle", timeout=60000)
                html = await page.content()
                emails = re.findall(email_regex, html)
                for email in emails:
                    if email.lower() == "user@domain.com":
                        print("   ⚠️ Skipped dummy email: user@domain.com")
                        continue

                    found_emails.add(email)
                    print(f"   ✅ Added email: {email}")

            except Exception as e:
                print(f"   ❌ Failed for {url}: {e}")
                continue

        await browser.close()

    print(f"\n🏁 FINAL EMAIL LIST: {list(found_emails)}")
    return list(found_emails)

@function_tool
async def extract_and_save_leads(location, keyword, max_items=10):
    print("Tool Called: Extract and Save Leads")
    try:
        # 1️⃣ Start Actor
        actor_input = {
            "searchStringsArray": [f"{keyword} in {location}"],
            "maxCrawledPlacesPerSearch": max_items,
            "language": "en",
            "proxy": {"useApifyProxy": True},
        }
        run = client.actor(ACTOR_ID).call(run_input=actor_input)
        dataset_id = run.get("defaultDatasetId")
        if not dataset_id:
            return "No dataset returned by Actor."

        # 2️⃣ Fetch items
        items = client.dataset(dataset_id).list_items().items
        if not items:
            return "No items found in dataset."

        # 3️⃣ Save to CSV
        filename = f"leads_{uuid.uuid4().hex}.csv"
        fieldnames = ["name", "url", "phone", "email", "address", "placeId"]

        with open(filename, mode="w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for item in items:
                website = item.get("website")
                try:
                    email = await extract_emails_fast_async(website) if website else ""
                except Exception as e:
                    print(f"Email extraction failed for {website}: {e}")
                    email = ""
                writer.writerow({
                    "name": item.get("title") or item.get("name"),
                    "url": website or item.get("url"),
                    "phone": item.get("phone"),
                    "email": ", ".join(email) if isinstance(email, list) else email,
                    "address": item.get("address"),
                    "placeId": item.get("placeId"),
                })

        print(f"Saved {len(items)} items to {filename}")
        return f"Saved {len(items)} items to {filename}"

    except Exception as e:
        print("Error:", e)
        return f"Error occurred: {e}"

# BAD_SITES = [
#     "tripadvisor", "michelin", "reddit", "visitqatar",
#     "blog", "guide", "top", "best", "seasonedtraveller",
#     "50best", "culturetrip", "facebook", "instagram",
#     "youtube", "pinterest", "wikipedia", "linkedin"
# ]

# ALLOWED_EXTENSIONS = [".com", ".net", ".org", ".qa", ".co", ".us", ".uk"]

# EMAIL_REGEX = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"

# PHONE_REGEX = r"\+?\d[\d\-\(\)\s]{7,15}"

# def debug(msg):
#     print(f"[DEBUG] {msg}")


# @function_tool
# def search_web(niche: str):
#     debug(f"search_web() called with niche = {niche}")

#     api_key = os.getenv("SERPER_API")
#     if not api_key:
#         debug("Missing SERPER API KEY")
#         return []

#     url = "https://google.serper.dev/maps"

#     payload = {"q": niche}
#     headers = {
#         "X-API-KEY": api_key,
#         "Content-Type": "application/json"
#     }

#     try:
#         res = requests.post(url, json=payload, headers=headers, timeout=20)
#         data = res.json()

#         places = data.get("places", [])
#         debug(f"Found {len(places)} places from Serper Maps")

#         websites = []
#         for p in places:
#             w = p.get("website")
#             if w:
#                 websites.append(w)

#         # Filter websites
#         final = []
#         for w in websites:
#             lower = w.lower()
#             if any(bad in lower for bad in BAD_SITES):
#                 continue
#             if not any(lower.endswith(ext) for ext in ALLOWED_EXTENSIONS):
#                 continue
#             final.append(w)

#         debug(f"Filtered to {len(final)} real business websites")
#         return list(set(final))

#     except Exception as e:
#         debug(f"Serper ERROR = {e}")
#         return []

# # ===========================================================
# # 2) SCRAPE EMAILS + PHONES FROM EXTRACTED WEBSITES
# # ===========================================================
# @function_tool
# def scrape_multiple_urls(urls: list):
#     debug(f"scrape_multiple_urls() called with {len(urls)} URLs")

#     all_data = []

#     for url in urls:
#         debug(f"Fetching: {url}")

#         try:
#             r = requests.get(url, timeout=12, headers={"User-Agent": "Mozilla/5.0"})
#             html = r.text
#         except Exception as e:
#             debug(f"Fetch error: {e}")
#             continue

#         # Emails
#         emails = list(set(re.findall(EMAIL_REGEX, html)))

#         # Phones Clean
#         raw = re.findall(PHONE_REGEX, html)
#         phones = []
#         for p in raw:
#             num = re.sub(r"\D", "", p)
#             if 7 <= len(num) <= 15:
#                 phones.append("+" + num if not p.startswith("+") else p)

#         phones = list(set(phones))

#         debug(f"Emails={len(emails)} Phones={len(phones)}")

#         all_data.append({
#             "url": url,
#             "emails": emails,
#             "phones": phones
#         })

#         time.sleep(0.4)

#     return all_data

# # @function_tool
# # def fetch_html(url: str):
# #     debug(f"fetch_html() called with URL = {url}")

# #     try:
# #         res = requests.get(url, timeout=8, headers={"User-Agent": "Mozilla/5.0"})
# #         debug(f"fetch_html() received {len(res.text)} characters HTML")
# #         return res.text
# #     except Exception as e:
# #         debug(f"fetch_html() ERROR = {e}")
# #         return ""


# # @function_tool
# # def extract_contacts(html: str):
# #     debug("extract_contacts() called")

# #     if not html:
# #         debug("extract_contacts() received empty HTML")
# #         return {"emails": [], "phones": []}

# #     emails = list(set(re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", html)))
# #     phones = list(set(re.findall(r"\+?\d[\d\-\s]{8,}\d", html)))

# #     debug(f"extract_contacts() found {len(emails)} emails and {len(phones)} phones")

# #     return {
# #         "emails": emails,
# #         "phones": phones
# #     }


# @function_tool
# def save_csv(data: list):
#     debug(f"save_csv() called, saving {len(data)} leads")

#     filename = f"leads_{uuid.uuid4().hex[:8]}.csv"
    
#     try:
#         with open(filename, "w", newline="", encoding="utf-8") as f:
#             writer = csv.writer(f)
#             writer.writerow(["url", "emails", "phones"])

#             for row in data:
#                 writer.writerow([
#                     row["url"],
#                     ", ".join(row["emails"]),
#                     ", ".join(row["phones"])
#                 ])

#         debug(f"save_csv() completed, file = {filename}")
#         return f"CSV saved as {filename}"
#     except Exception as e:
#         debug(f"save_csv() ERROR = {e}")
#         return "CSV saving failed"


# @function_tool
# def validate_leads(leads: list):
#     debug(f"validate_leads() called with {len(leads)} leads")

#     seen = set()
#     cleaned = []

#     for item in leads:
#         key = (item["url"], tuple(item["emails"]), tuple(item["phones"]))
#         if key in seen:
#             debug(f"Duplicate ignored: {item['url']}")
#             continue

#         item["phones"] = [p.replace(" ", "") for p in item["phones"]]
#         cleaned.append(item)
#         seen.add(key)

#     debug(f"validate_leads() output leads: {len(cleaned)}")
#     return cleaned


# def extract_links(html: str):
#     debug("extract_links() called")

#     soup = BeautifulSoup(html, "html.parser")
#     links = []

#     for a in soup.find_all("a", href=True):
#         url = a["href"]
#         if "restaurant" in url:
#             links.append(url)

#     links = list(set(links))
#     debug(f"extract_links() found {len(links)} restaurant links")
#     return links
