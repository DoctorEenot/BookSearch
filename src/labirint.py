from .book import Book
from bs4 import BeautifulSoup
import requests
from typing import List
from .search_engine import SearchEngine
import urllib
import time

BASE_URL = "https://www.labirint.ru"


class Labirint(SearchEngine):

    def search_book(name: str, cover: str, max_per_name: int) -> List[Book] | None:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36',
            'Connection': 'keep-alive'
        }

        url = f"{BASE_URL}/search/{name}/"

        page_raw = ''
        while True:
            try:
                response = requests.get(
                    url, headers=headers, stream=True)

                page_raw = response.text
                break
            except:
                # break
                pass

        if response.status_code != 200 or len(page_raw) == 0:
            raise Exception("Response status is not 200")

        page = BeautifulSoup(page_raw, 'html.parser')

        search_error = page.find('div', class_='search-error')
        if search_error is not None:
            return None

        products_tag = page.find('div', class_="products-row")

        if products_tag is None:
            return None

        products = [product for product in products_tag.findChildren(
            "div", recursive=False)]

        to_return = []

        headers['Referer'] = urllib.parse.quote(url)

        for product_tag in products:
            if len(to_return) == max_per_name:
                break
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

            if not Labirint.verify_name(name, book_name):
                continue

            book_dir = f"{BASE_URL}/{product['data-dir']}/{product['data-product-id']}"

            page_raw = ''
            while True:
                try:
                    response = requests.get(
                        book_dir, headers=headers, stream=True)

                    page_raw = response.text
                    break
                except:
                    # break
                    pass

            if response.status_code != 200 or len(page_raw) == 0:
                raise Exception("Response status is not 200")

            # for data in response.iter_content(chunk_size=1024):
            #     pass

            page = BeautifulSoup(page_raw, 'html.parser')

            publisher_tag = page.find("div", attrs={"class": "publisher"})
            year = 0
            if publisher_tag != None:
                children = list(publisher_tag.children)
                if len(children) != 0:
                    year_raw = children[-1].text
                    if 'г.' in year_raw:
                        chunks = year_raw.split(' ')
                        for chunk in chunks:
                            try:
                                year = int(chunk)
                            except:
                                pass

            about = page.find(
                "div", attrs={"id": "fullannotation"})

            if about is None:
                about = page.find(
                    "div", attrs={"id": "product-about"})

            if about is None:
                about = ""
            else:
                about = about.findChild("p")
                if about == None:
                    about = ""
                else:
                    about = about.text.replace('\n', '').strip()

            price_tag = page.find(
                "span", attrs={"class": "buying-pricenew-val-number"}
            )
            price = 0
            if price_tag is not None:
                price = int(price_tag.text)

            if not Labirint.verify_name(name, book_name):
                continue

            to_return.append(
                Book(author, book_name, year, about, genre, cover, price))

        return to_return
