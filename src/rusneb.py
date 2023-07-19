from .search_engine import SearchEngine
from typing import List
from .book import Book
import requests as rq
from bs4 import BeautifulSoup
from fake_headers import Headers

BASE_URL = "https://rusneb.ru/search/?q={}"


class RusNeb(SearchEngine):
    def search_book(name: str, cover: str, max_per_name: int) -> List[Book] | None:
        s = rq.Session()
        header = Headers(browser="chrome",headers=True).generate()
        response = s.get(BASE_URL.format(name), headers=header)
        if response.status_code != 200:
            raise Exception(
                f"Response status for main page is not 200, but {response.status_code}") 
        page = BeautifulSoup(response.text, 'html.parser')
        objects_tag = page.findAll('div', class_='search-list')
        if objects_tag == []:
            return None
        books = []
        for objects in objects_tag:
            for object in objects.find_all('div', class_="search-list__item search-result__content-list-kind relative"):
                id = 1
                # обьект книги
                for data in object.find_all("div", class_="search-list__item_column"):
                    if id == 1:
                        try:
                            url = data.find("p").find("a", href=True)['href']
                            if not url == "javascript:void(0);":
                                books.append(url)
                            id += 1
                        except:
                            pass
        return RusNeb.__get_data(s, books, header)
    def __get_data(session, urls, header):
        books = []
        for url in urls:
            url_base = "https://rusneb.ru" + url
            res = session.get(url_base, headers=header)
            if res.status_code != 200:
                raise Exception(
                    f"Response status for main page is not 200, but {res.status_code}")
            page = BeautifulSoup(res.text, 'html.parser')
            try:
                author = str(" ".join(page.find('div', class_='title title--work').text.split()))
            except:
                author = ""
            try:
                name = str(page.find("div", class_="cards__author").find("a").text)
            except: 
                name = ""
            try:
                year = int(page.find("span", itemprop="datePublished").text)
            except:
                year = 0
            books.append(Book(author, name, year, "", "", "", 2000))
        return books
