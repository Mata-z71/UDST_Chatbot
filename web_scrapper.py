import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import pandas as pd
from tqdm import tqdm
import time


BASE_URL = "https://www.udst.edu.qa"
MAX_PAGES = 100  # limit to avoid scraping too many pages
CHUNK_SIZE = 500


visited = set()
to_visit = [BASE_URL]

documents = []


def clean_text(text):
    text = text.replace("\n", " ")
    text = text.replace("\t", " ")
    text = " ".join(text.split())
    return text


def chunk_text(text, chunk_size=CHUNK_SIZE, overlap=50):
    words = text.split()
    chunks = []
    if chunk_size <= overlap:
        raise ValueError("chunk_size must be greater than overlap")

    i = 0
    while i < len(words):
        chunk = " ".join(words[i:i + chunk_size])
        chunks.append(chunk)
        if i + chunk_size >= len(words):
            break
        i += chunk_size - overlap

    return chunks


def extract_text(url):

    try:
        response = requests.get(url, timeout=10)
    except:
        return ""

    soup = BeautifulSoup(response.text, "html.parser")

    # remove scripts and styles
    for tag in soup(["script", "style", "noscript"]):
        tag.extract()

    text = soup.get_text()

    return clean_text(text)


def get_links(url):

    links = []

    try:
        response = requests.get(url, timeout=10)
    except:
        return links

    soup = BeautifulSoup(response.text, "html.parser")

    for a in soup.find_all("a", href=True):

        href = a["href"]

        full_url = urljoin(url, href)

        parsed = urlparse(full_url)

        # keep only internal links
        if parsed.netloc == urlparse(BASE_URL).netloc:

            # remove fragments
            clean_url = full_url.split("#")[0]

            links.append(clean_url)

    return links


def crawl():

    while to_visit and len(visited) < MAX_PAGES:

        url = to_visit.pop(0)

        if url in visited:
            continue

        print("Scraping:", url)

        visited.add(url)

        text = extract_text(url)

        if len(text) > 200:

            chunks = chunk_text(text)

            for chunk in chunks:

                documents.append({
                    "source": url,
                    "text": chunk
                })

        links = get_links(url)

        for link in links:

            if link not in visited and link not in to_visit:
                to_visit.append(link)

        time.sleep(1)


def save_dataset(output_csv="website_data.csv"):

    df = pd.DataFrame(documents)

    df.to_csv(output_csv, index=False)

    print("Saved dataset with", len(df), "chunks to", output_csv)


if __name__ == "__main__":

    crawl()

    save_dataset(output_csv="website_data.csv")