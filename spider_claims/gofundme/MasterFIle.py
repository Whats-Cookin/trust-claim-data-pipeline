import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
from datetime import date


def remove_duplicate_words(text):
    words = text.split()
    seen = set()
    result = []
    for word in words:
        if word.lower() not in seen:
            seen.add(word.lower())
            result.append(word)
    return " ".join(result)


def remove_query_params(url):
    query_index = url.find("?")
    if query_index != -1:
        url = url[:query_index]
    return url


def get_gofundme_urls(seed_url, max_pages=100, output_file="gofundme_urls.txt"):
    visited_urls = set()
    try:
        with open(output_file, "r") as f:
            for line in f:
                visited_urls.add(line.strip())
    except FileNotFoundError:
        pass

    urls_to_visit = [seed_url]
    gofundme_urls = set()

    urls_scraped = 0

    while urls_to_visit and urls_scraped < max_pages:
        current_url = urls_to_visit.pop(0)

        if current_url in visited_urls:
            continue

        try:
            print(f"Scraping: {current_url}")
            response = requests.get(current_url)
            visited_urls.add(current_url)

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")
                links = soup.find_all("a", href=True)

                for link in links:
                    url = link["href"]
                    if re.match(r"^https://www.gofundme.com/f/.*$", url):
                        gofundme_urls.add(url)
                        urls_scraped += 1
                        print(f"Found GoFundMe URL: {url} ({urls_scraped}/{max_pages})")
                    elif url.startswith("/") and not url.startswith("//"):
                        url = f"https://www.gofundme.com{url}"
                        urls_to_visit.append(url)

        except Exception as e:
            print(f"Error accessing {current_url}: {e}")

    if not urls_to_visit:
        print("No more pages to scrape.")
    with open(output_file, "w") as f:
        for url in gofundme_urls:
            f.write("%s\n" % url)

    return list(gofundme_urls)


def clean_urls(input_file, output_file):
    with open(input_file, "r") as input_file, open(output_file, "w") as output_file:
        for line in input_file:
            url = line.strip()
            clean_url = remove_query_params(url)
            output_file.write(clean_url + "\n")


def duplicate_and_modify_urls_from_file(filename):
    modified_urls = []
    with open(filename, "r") as file:
        urls = file.readlines()
        for url in urls:
            url = url.strip()
            modified_urls.append(url)
            modified_url = url + "?modal=donations&tab=all"
            modified_urls.append(modified_url)

    with open("modified_urls.txt", "w") as output_file:
        for modified_url in modified_urls:
            output_file.write(modified_url + "\n")


def scrape_data(url):
    try:
        page_to_scrape = requests.get(url)
        page_to_scrape.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL '{url}': {e}")
        return None

    soup = BeautifulSoup(page_to_scrape.text, "html.parser")

    title = soup.find("h1", class_="hrt-mb-0 p-campaign-title")
    if title:
        title = title.text.strip()
        title = remove_duplicate_words(title)
    else:
        title = "Title not found"

    statement_divs = soup.find_all("div", class_="campaign-description_content__C1C_5")
    statement = "\n".join([div.text.strip() for div in statement_divs])
    statement = remove_duplicate_words(statement)

    progress_meter = soup.find(
        "div", class_="progress-meter_progressMeterHeading__A6Slt"
    )
    if progress_meter:
        amount_raised_element = progress_meter.find("div", class_="hrt-disp-inline")
        goal_amount_element = progress_meter.find(
            "span", class_="hrt-text-body-sm hrt-text-gray"
        )

        amount_raised = (
            amount_raised_element.text.strip()
            if amount_raised_element
            else "Amount not found"
        )
        goal_amount = (
            re.search(r"(\d[\d.,]*)", goal_amount_element.text.strip()).group()
            if goal_amount_element
            and re.search(r"(\d[\d.,]*)", goal_amount_element.text.strip())
            else "Goal amount not found"
        )
    else:
        amount_raised = "Amount not found"
        goal_amount = "Goal amount not found"

    donors = soup.find_all("div", class_="hrt-avatar-lockup-content")
    donations = []
    for donor in donors:
        donor_name = donor.find("div").text.strip()
        donation_amount_element = donor.find("span", class_="hrt-font-bold")
        donation_amount = (
            donation_amount_element.text.strip()
            if donation_amount_element
            else "Donation amount not found"
        )
        donations.append({"Donor Name": donor_name, "Donation Amount": donation_amount})

    return {
        "Title": title,
        "Statement": statement,
        "Amount Raised": amount_raised,
        "Goal Amount": goal_amount,
        "Donations": donations,
        "Source URL": url,
        "Date Scraped": date.today(),
    }


def read_urls_from_file(filename):
    try:
        with open(filename, "r") as file:
            urls = [line.strip() for line in file.readlines()]
        return urls
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")
        return []


# Merge the functionalities
seed_url = "https://www.gofundme.com/discover"
get_gofundme_urls(seed_url, max_pages=100)
clean_urls("gofundme_urls.txt", "cleaned_gofundme_urls.txt")
duplicate_and_modify_urls_from_file("cleaned_gofundme_urls.txt")
url_pairs = read_urls_from_file("modified_urls.txt")

csv_filename = "gofundme_scraped_data.csv"
data_list = []
for full_url in url_pairs:
    scraped_data = scrape_data(full_url)
    if scraped_data:
        data_list.append(scraped_data)

df = pd.DataFrame(
    data_list,
    columns=[
        "Title",
        "Statement",
        "Amount Raised",
        "Goal Amount",
        "Donations",
        "Source URL",
        "Date Scraped",
    ],
)

df_filtered = df[df["Source URL"].str.endswith("tab=all")]

df_filtered.to_csv(csv_filename, index=False)
print(f"Data scraped and saved successfully in CSV file '{csv_filename}'!")
