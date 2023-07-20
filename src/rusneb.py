from .search_engine import SearchEngine
from typing import List, Tuple, Dict
from .book import Book
import requests
from bs4 import BeautifulSoup
from fake_headers import Headers

BASE_URL = "https://rusneb.ru"


class RusNeb(SearchEngine):
    def search_book(name: str, cover: str, max_per_name: int) -> List[Book] | None:
        global BASE_URL

        session = requests.Session()
        header = Headers(browser="firefox", headers=True).generate()
        header['Connection'] = 'keep-alive'

        response = session.get(
            f"{BASE_URL}/search/?q={name}", headers=header, stream=True)

        if response.status_code != 200:
            raise Exception(
                f"Response status for main page is not 200, but {response.status_code}")

        page = BeautifulSoup(response.text, 'html.parser')
        search_list = page.find('div', class_='search-list')

        books = []
        for object in search_list.find_all('div', class_="search-list__item search-result__content-list-kind relative", limit=max_per_name):
            book_url = object.find(
                "div", class_="search-list__item_column").find('a', href=True)['href']
            book = RusNeb.__get_book(session, book_url, header, cover)
            books.append(book)

        return books

    def __get_book(session: requests.Session, url: str, headers: Headers, cover: str) -> Book:
        res = session.get(f"{BASE_URL}{url}", headers=headers, stream=True)
        if res.status_code != 200:
            raise Exception(
                f"Response status for main page is not 200, but {res.status_code}")

        page = BeautifulSoup(res.text, 'html.parser')
        try:
            book_name = " ".join(
                page.find('div', class_='title title--work').text.split())
        except:
            book_name = ""

        try:
            author = page.find(
                "div", class_="cards__author").find("a").text
        except:
            author = ""

        # parse description
        try:
            cards = page.find(
                'div', class_='content cards-content').find_all('p', limit=2)
            description = ""

            for card in cards:
                description += card.text
        except Exception as e:
            description = ""

        return Book(author, book_name, 0, description, '', cover, 2000)
