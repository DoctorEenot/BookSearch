from .search_engine import SearchEngine
from typing import List
from .book import Book
import requests
from bs4 import BeautifulSoup
from fake_headers import Headers

BASE_URL = "https://slovo-shop.ru"


class JivoeSlovo(SearchEngine):
    def search_book(name: str, cover: str, max_per_name: int) -> List[Book] | None:
        global BASE_URL

        session = requests.Session()
        header = Headers(browser="firefox", headers=True).generate()
        header['Connection'] = 'keep-alive'

        response = session.get(
            f"{BASE_URL}/index.php?route=product/search&search={name}", headers=header, stream=True)

        if response.status_code != 200:
            raise Exception(
                f"Response status for main page is not 200, but {response.status_code}")

        page = BeautifulSoup(response.text, 'html.parser')
        books = []
        for div in page.find_all('div', class_='name', limit=max_per_name):
            book_url = div.find("a", href=True)['href']
            book = JivoeSlovo.__get_book(session, book_url, header, cover)
            books.append(book)

        return books

    def __get_book(session: requests.Session, url: str, headers: Headers, cover: str) -> Book:
        res = session.get(f"{url}", headers=headers, stream=True)
        if res.status_code != 200:
            raise Exception(
                f"Response status for main page is not 200, but {res.status_code}")

        page = BeautifulSoup(res.text, 'html.parser')
        try:
            book_name = " ".join(
                page.find(
                "h1", itemprop="name").text.split())
        except:
            book_name = ""
        author = ""
        try:
            for data in page.find("table", class_="short-attr-table").find_all("tbody"):
                if data.find("td", class_="left").find("span").text == "Автор":
                    author = data.find("td", class_="right").find("span").text
        except:
            pass
        try:
            description = " ".join(page.find('div', itemprop="description").text.split())
        except:
            description = ""
        try:
            price = int(page.find('div', class_='priceBig').find("span").text[:-5])
        except:
            price = 2000
        
        return Book(author, book_name, 0, description, '', cover, price)
