from .search_engine import SearchEngine
from typing import List, Tuple, Dict
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
        return RusNeb.__out_book(RusNeb.__get_data(s, books, header))
    def __get_data(session, urls, header):
        books = {}
        for url in urls:
            url_base = "https://rusneb.ru" + url
            res = session.get(url_base, headers=header)
            if res.status_code != 200:
                raise Exception(
                    f"Response status for main page is not 200, but {res.status_code}")
            page = BeautifulSoup(res.text, 'html.parser')
            try:
                name_book = " ".join(page.find('div', class_='title title--work').text.split())
            except:
                name_book = None
            try:
                autor_book = page.find("div", class_="cards__author").find("a").text
            except: 
                autor_book = None
            try:
                date_book = page.find("span", itemprop="datePublished").text
            except:
                date_book = None
            books[len(books)] = [url_base, name_book, autor_book, date_book]
        return books
    def __out_book(books):
        datas = []
        for x in range(len(books)):
            data = []
            if books[x][1] is None:
                data.append("")
            else:
                data.append(str(books[x][1]))
            if books[x][2] is None:
                data.append("")
            else:
                data.append(str(books[x][2]))
            if books[x][3] is None:
                data.append("")
            else:
                data.append(int(books[x][3]))
            datas.append(Book(data[0], data[1], data[2], "", "", "", 2000))
        return datas
