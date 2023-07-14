from .search_engine import SearchEngine
from typing import List, Tuple, Dict
from .book import Book
import requests
import re
from bs4 import BeautifulSoup

BASE_URL = "https://www.livelib.ru"


class Livelib(SearchEngine):
    def search_book(name: str, cover: str, max_per_name: int) -> List[Book] | None:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36',
            'Referer': 'https://www.livelib.ru/'
        }

        request_url = f"{BASE_URL}/find/{name}"

        response = requests.get(request_url, headers=headers)

        if response.status_code != 200:
            raise Exception(
                f"Response status for main page is not 200, but {response.status_code}")

        page = BeautifulSoup(response.text, 'html.parser')

        objects_tag = page.find('div', attrs={'id': 'objects-block'})

        if objects_tag == None:
            return None

        to_return: List[Book] = []

        books = objects_tag.findChildren('div', class_="ll-redirect-book")
        for book in books[:max_per_name]:
            link: str = book["data-link"]

            response = requests.get(f"{BASE_URL}{link}", headers=headers)

            if response.status_code != 200:
                raise Exception("Response status is not 200")

            page_text = response.content.decode()

            book_page = BeautifulSoup(page_text, 'html.parser')

            header_tag = book_page.find('section', class_='bc-header__wrap')

            book_name = header_tag.findChild(
                'h1').text

            author = header_tag.findChild('h2', class_='bc-author').text

            description_tag = book_page.find(
                'div', attrs={'id': 'lenta-card__text-edition-escaped'})
            description = ''
            if description_tag != None:
                description = description_tag.text

            to_return.append(
                Book(author, book_name, 0, description, '', cover, 0))

        if len(to_return) == 0:
            return None

        return to_return
