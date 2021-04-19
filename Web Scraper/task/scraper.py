import requests
from bs4 import BeautifulSoup
import string
import os
import shutil

main_page_url = "https://www.nature.com/nature/articles?searchType=journalSearch&sort=PubDate&page="
base_url = "https://www.nature.com"
relative_paths = []
absolute_paths = []


def scrape_article_links(site_url, article_type):
    links = []
    headers = {"Accept-Language": "en-US, en; q=0.5"}
    r = requests.get(site_url, headers=headers)

    if r.status_code == 200:
        try:
            soup = BeautifulSoup(r.content, "html.parser")
            articles = soup.find_all("article")
            for container in articles:
                if container.find("span", {"class": "c-meta__type"}).text == article_type:
                    link = container.find("h3", {"class": "c-card__title", "itemprop": "name headline"}).find("a").get(
                        'href')
                    links.append(link)
        except:
            print("Error scraping links to articles on ", site_url)
    else:
        print("Error when making request to catalogue page ", site_url)
    return links


def get_absolute_paths(relative_paths, base_url):
    absolute_paths = []
    for path in relative_paths:
        absolute_paths.append(base_url + path)
    return absolute_paths


def parse_title(some_str):
    translator = str.maketrans(" ", "_", string.punctuation)
    parsed_string = ""
    if some_str:
        parsed_string = some_str.translate(translator)
        parsed_string = parsed_string + ".txt"
    return parsed_string


def scrape_article_text(article_link):
    containers = []
    article_text = None
    title = None

    r = requests.get(article_link)
    if r.status_code == 200:
        soup = BeautifulSoup(r.content, "html.parser")
        containers.append(soup.find("div", {"class": "article__body cleared"}))
        containers.append(soup.find("div", {"class": "c-article-body"}))
        containers.append(soup.find("div", {"class": "article-item__body"}))
        containers.append(soup.find("div", {"id": "content", "class": "hentry article"}))
        allocated_containers = [div for div in containers if div]
        if len(allocated_containers) > 0:
            try:
                article_text = allocated_containers[0].get_text().strip()
                title = soup.find("meta", {"name": "dc.title"})['content']
            except:
                print("Error")
        if title:
            title = parse_title(title)
    else:
        print("The div with the text content couldn't be found")
    return [title, article_text]


def save_article_to_file(title, contents):
    if title and contents:
        try:
            with open(title, "wb") as file:
                file.write(bytes(contents, encoding="utf-8"))
        except:
            print("Error saving to file")
    else:
        print("title or contents missing")


def cleanup_old_folders():
    article_folders = [file for file in os.listdir() if file.startswith("Page_")]
    for folder in article_folders:
        try:
            shutil.rmtree(folder)
        except OSError:
            os.remove(folder)


num_pages = int(input())
article_type = input()

path_parent = os.getcwd()
cleanup_old_folders()
print()

for counter in range(1, num_pages + 1):
    page_url = main_page_url + str(counter)
    relative_paths = scrape_article_links(page_url, article_type)

    page_folder = "Page_{}".format(counter)
    if not os.access(page_folder, os.F_OK):
        os.mkdir(page_folder)
    os.chdir(page_folder)

    if len(relative_paths) > 0:
        #print("Found {} links for page {}".format(len(relative_paths), counter))
        absolute_paths = get_absolute_paths(relative_paths, base_url)
        for article in absolute_paths:
            data = scrape_article_text(article)
            save_article_to_file(data[0], data[1])
    else:
        print("No articles found for page: ", counter)

    os.chdir(path_parent)
