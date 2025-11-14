from agents import function_tool
import requests
from bs4 import BeautifulSoup
import re
import csv
import uuid
import time


def debug(msg: str):
    print(f"[DEBUG] {msg}")


@function_tool
def search_web(niche: str):
    debug(f"search_web() called with niche = {niche}")

    api_key = "63950122c7fb8a9a2438e6f6e43f219bf87d5e35ef7b3c7b4b61c5aaaa0351ab"
    params = {
        "q": niche,
        "engine": "google",
        "api_key": api_key,
        "num": 10
    }

    try:
        response = requests.get("https://serpapi.com/search.json", params=params)
        debug("search_web() SERPAPI request success")
        data = response.json()
        urls = [result["link"] for result in data.get("organic_results", [])]
        debug(f"search_web() extracted {len(urls)} URLs")
        return urls
    except Exception as e:
        debug(f"search_web() ERROR = {e}")
        return []


@function_tool
def scrape_multiple_urls(urls: list):
    debug(f"scrape_multiple_urls() called with {len(urls)} URLs")
    all_contacts = []

    phone_pattern = r"(?:\+?\d{1,3}[-\s]?)?(?:\(?\d{2,4}\)?[-\s]?)?\d{6,12}"

    for url in urls:
        debug(f"Fetching URL: {url}")
        try:
            res = requests.get(url, timeout=8, headers={"User-Agent": "Mozilla/5.0"})
            html = res.text
            debug(f"Received {len(html)} chars HTML")
        except Exception as e:
            debug(f"Error fetching {url} = {e}")
            continue

        # Emails
        emails = list(set(re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", html)))

        # Phones
        phones = list(set(re.findall(phone_pattern, html)))
        phones = [p for p in phones if 6 <= len(re.sub(r"\D", "", p)) <= 15]

        debug(f"Found {len(emails)} emails and {len(phones)} phones")

        all_contacts.append({
            "url": url,
            "emails": emails,
            "phones": phones
        })

        time.sleep(0.5)

    debug(f"Total URLs processed: {len(all_contacts)}")
    return all_contacts


# @function_tool
# def fetch_html(url: str):
#     debug(f"fetch_html() called with URL = {url}")

#     try:
#         res = requests.get(url, timeout=8, headers={"User-Agent": "Mozilla/5.0"})
#         debug(f"fetch_html() received {len(res.text)} characters HTML")
#         return res.text
#     except Exception as e:
#         debug(f"fetch_html() ERROR = {e}")
#         return ""


# @function_tool
# def extract_contacts(html: str):
#     debug("extract_contacts() called")

#     if not html:
#         debug("extract_contacts() received empty HTML")
#         return {"emails": [], "phones": []}

#     emails = list(set(re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", html)))
#     phones = list(set(re.findall(r"\+?\d[\d\-\s]{8,}\d", html)))

#     debug(f"extract_contacts() found {len(emails)} emails and {len(phones)} phones")

#     return {
#         "emails": emails,
#         "phones": phones
#     }


@function_tool
def save_csv(data: list):
    debug(f"save_csv() called, saving {len(data)} leads")

    filename = f"leads_{uuid.uuid4().hex[:8]}.csv"
    
    try:
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["url", "emails", "phones"])

            for row in data:
                writer.writerow([
                    row["url"],
                    ", ".join(row["emails"]),
                    ", ".join(row["phones"])
                ])

        debug(f"save_csv() completed, file = {filename}")
        return f"CSV saved as {filename}"
    except Exception as e:
        debug(f"save_csv() ERROR = {e}")
        return "CSV saving failed"


@function_tool
def validate_leads(leads: list):
    debug(f"validate_leads() called with {len(leads)} leads")

    seen = set()
    cleaned = []

    for item in leads:
        key = (item["url"], tuple(item["emails"]), tuple(item["phones"]))
        if key in seen:
            debug(f"Duplicate ignored: {item['url']}")
            continue

        item["phones"] = [p.replace(" ", "") for p in item["phones"]]
        cleaned.append(item)
        seen.add(key)

    debug(f"validate_leads() output leads: {len(cleaned)}")
    return cleaned


def extract_links(html: str):
    debug("extract_links() called")

    soup = BeautifulSoup(html, "html.parser")
    links = []

    for a in soup.find_all("a", href=True):
        url = a["href"]
        if "restaurant" in url:
            links.append(url)

    links = list(set(links))
    debug(f"extract_links() found {len(links)} restaurant links")
    return links
