from .search_engine import SearchEngine
from typing import List, Tuple, Dict
from .book import Book
import requests
import re
from bs4 import BeautifulSoup
from fake_headers import Headers

BASE_URL = "https://knijky.ru"

NAMES = ["views-row views-row-1 views-row-odd views-row-first", "views-row views-row-2 views-row-even", "views-row views-row-3 views-row-odd", "views-row views-row-4 views-row-even", "views-row views-row-5 views-row-odd", "views-row views-row-6 views-row-even", "views-row views-row-7 views-row-odd", "views-row views-row-8 views-row-even", "views-row views-row-9 views-row-odd", "views-row views-row-10 views-row-even views-row-last"]


class Knijky(SearchEngine):
    def search_book(name: str, cover: str, max_per_name: int) -> List[Book] | None:
        global BASE_URL
        global NAMES

        session = requests.Session()
        header = Headers(browser="firefox", headers=True).generate()
        header['Connection'] = 'keep-alive'

        response = session.get(f"https://knijky.ru/search?search_api_views_fulltext={name}", headers=header, stream=True)

        if response.status_code != 200:
            raise Exception(
                f"Response status for main page is not 200, but {response.status_code}")

        page = BeautifulSoup(response.text, "html.parser")
        search_list1 = page.find("div", class_="view-content")
        if search_list1 == None:
            return []
        blocks = []
        for name in NAMES:
            block = search_list1.find("div", name)
            if block:
                blocks.append(block)

        books = []
        if max_per_name > len(blocks):
            max_per_name = len(blocks)
        for number in range(max_per_name):
            temp1 = blocks[number].find("div", class_="col-lg-3 col-md-3 col-sm-3")
            temp2 = temp1.find("div", class_="views-field views-field-field-book-photo")
            temp3 = temp2.find("span", class_="field-content")
            book_url = temp3.find('a', href=True)['href']
            bookss = Knijky.__get_book(session, book_url, header, cover)
            books.append(bookss)

        return books

    def __format_text(text: str) -> str:
        return text.replace('\n', '').replace('\t', '').replace('   ', '').replace("  ", " ").strip()

    def __get_book(session: requests.Session, url: str, headers: Headers, cover: str) -> Book:
        res = session.get(f"{BASE_URL}{url}", headers=headers, stream=True)
        if res.status_code != 200:
            raise Exception(
                f"Response status for main page is not 200, but {res.status_code}")

        page = BeautifulSoup(res.text, 'html.parser')
        listed = page.find("div", "content clearfix")
        try:
            book_name = Knijky.__format_text(listed.find("h1", class_="title").text)
        except:
            book_name = ""

        listed = page.find("div", "info_block col-lg-9 col-md-9 col-sm-9")
        lines = listed.find_all("div", "line")

        try:
            author = Knijky.__format_text(lines[0].find(
                "span", class_="left").text).replace("Автор: ", "")
        except:
            author = ""

        # жанр
        try:
            genre = Knijky.__format_text(lines[1].find(
                "span", class_="right").text).replace("Жанр: ", "")
        except:
            genre = ""
        old = 0
        for block in lines:
            data = block.find("span", "right")
            if data:
                content = Knijky.__format_text(data.text)
                if content[:4] == "Дата":
                    old = int(content.replace("Дата написания: ", "").replace(" год", ""))
        return Book(author, book_name, old, "", genre, cover, 2000)