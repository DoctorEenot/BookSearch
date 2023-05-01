from .book import Book
from bs4 import BeautifulSoup
import requests
from typing import List

BASE_URL = "https://www.labirint.ru"


class Labirint:

    def search_book(name: str, cover: str) -> List[Book] | None:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}

        response = requests.get(
            f"{BASE_URL}/search/{name}/?stype=0", headers=headers)
        if response.status_code != 200:
            raise Exception("Response status is not 200")

        page = BeautifulSoup(response.text, 'html.parser')

        search_error = page.find('div', class_='search-error')
        if search_error is not None:
            return None

        products_tag = page.find('div', class_="products-row")

        if products_tag is None:
            return None

        products = [product for product in products_tag.findChildren(
            "div", recursive=False)]

        to_return = []

        for product_tag in products[:3]:
            product = product_tag.findChild("div", class_="product")

            genre = product['data-maingenre-name']

            author_tag = product.findChild(
                "div", class_="product-author")
            if author_tag is None:
                author_tag = product.findChild(
                    "div", class_="product-pubhouse")

            author = author_tag.text.replace('\n', '').strip()

            book_name = product.findChild(
                'div', class_="product-cover").findChild('a', class_="product-title-link").text.replace('\n', '').strip()

            book_dir = f"{BASE_URL}/{product['data-dir']}/{product['data-product-id']}"

            response = requests.get(book_dir, headers=headers)
            if response.status_code != 200:
                raise Exception("Response status is not 200")

            page = BeautifulSoup(response.text, 'html.parser')

            about = page.find(
                "div", attrs={"id": "fullannotation"})

            if about is None:
                about = page.find(
                    "div", attrs={"id": "product-about"})

            about = about.findChild("p").text.replace('\n', '').strip()

            to_return.append(Book(author, book_name, 0, about, genre, cover))

        return to_return
