import requests
from bs4 import BeautifulSoup

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
    "Connection": "keep-alive",
}


def extract_gofundme_urls(url):
    response = requests.get(url, headers=headers)
    import pdb

    pdb.set_trace()
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, "html.parser")
        links = soup.find_all("a", href=True)
        gofundme_urls = [
            link["href"] for link in links if "gofundme.com" in link["href"]
        ]
        return gofundme_urls
    else:
        print("Failed to fetch the page:", response.status_code)
        return []


def save_urls_to_file(urls, filename):
    with open(filename, "w") as file:
        for url in urls:
            file.write(url + "\n")


if __name__ == "__main__":
    # search results page has more links
    # this searches for categories Nonprofit, Education, Animal, Environment, Community
    url = "https://www.gofundme.com/s?c=13&c=342&c=17&c=3&c=7"
    # "https://www.gofundme.com/"

    gofundme_urls = extract_gofundme_urls(url)

    save_urls_to_file(gofundme_urls, "gofundme_all_urls.txt")
