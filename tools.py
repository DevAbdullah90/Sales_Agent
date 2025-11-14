from agents import function_tool
import requests
from bs4 import BeautifulSoup
import re
import csv
import uuid


@function_tool
def search_web(niche: str):
    api_key = "63950122c7fb8a9a2438e6f6e43f219bf87d5e35ef7b3c7b4b61c5aaaa0351ab"
    params = {
        "q": niche,
        "engine": "google",
        "api_key": api_key,
        "num": 10
    }
    response = requests.get("https://serpapi.com/search.json", params=params)
    data = response.json()
    urls = [result["link"] for result in data.get("organic_results", [])]
    return urls



@function_tool
def fetch_html(url: str):
    """
    Fetch HTML content from any URL.
    """
    print(f"🌐 Fetching HTML from {url}")
    
    try:
        res = requests.get(url, timeout=8, headers={"User-Agent": "Mozilla/5.0"})
        return res.text
    except:
        return ""



@function_tool
def extract_contacts(html: str):
    """
    Extract email + phone numbers from HTML.
    """
    print("📬 Extracting contact info...")

    emails = list(set(re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", html)))
    phones = list(set(re.findall(r"\+?\d[\d\-\s]{8,}\d", html)))

    return {
        "emails": emails,
        "phones": phones
    }



@function_tool
def save_csv(data: list):
    """
    Save leads to CSV file.
    """
    filename = f"leads_{uuid.uuid4().hex[:8]}.csv"
    
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["url", "emails", "phones"])

        for row in data:
            writer.writerow([
                row["url"],
                ", ".join(row["emails"]),
                ", ".join(row["phones"])
            ])

    return f"CSV saved as {filename}"


@function_tool
def validate_leads(leads: list):
    seen = set()
    cleaned = []

    for item in leads:
        key = (item["url"], tuple(item["emails"]), tuple(item["phones"]))
        if key in seen: continue

        item["phones"] = [p.replace(" ", "") for p in item["phones"]]
        cleaned.append(item)
        seen.add(key)

    return cleaned


def extract_links(html: str):
    soup = BeautifulSoup(html, "html.parser")
    links = []
    for a in soup.find_all("a", href=True):
        url = a["href"]
        if "restaurant" in url:  # filter for restaurant pages
            links.append(url)
    return list(set(links))