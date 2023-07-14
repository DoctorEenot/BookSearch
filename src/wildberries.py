from .search_engine import SearchEngine
from typing import List, Tuple, Dict
from .book import Book
from enum import Enum
import requests
import re

BASE_URL = "https://search.wb.ru"

BASKETS = [
    (0, 143),  # 143
    (144, 287),  # 143
    (288, 431),  # 125
    (432, 719),  # 287
    (729, 1007),  # 278
    (1008, 1061),  # 53
    (1062, 1115),  # 53
    (1116, 1169),  # 53
    (1170, 1313),  # 143
    (1314, 1601),  # 287
    (1602, 1655)  # 53
]


class SubjectFiter(Enum):
    BOOKS = 381
    CAR_PARTS = 6728
    SECONDHAND_BOOKS = 3455


class Wildberries(SearchEngine):

    def get_basket(vol: int) -> str:
        for index, limits in enumerate(BASKETS):
            if vol >= limits[0] and vol <= limits[1]:
                return f"https://basket-{index+1:02d}.wb.ru"
        return f"https://basket-{len(BASKETS)}.wb.ru"

    def get_vol_part(id: int) -> Tuple[int, int]:
        return (id//100000, id//1000)

    def get_card_url(id: int) -> str:
        vol, part = Wildberries.get_vol_part(id)
        basket = Wildberries.get_basket(vol)

        return f"{basket}/vol{vol}/part{part}/{id}/info/ru/card.json"

    def search_book(name: str, cover: str, max_per_name: int) -> List[Book] | None:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}

        request_url = f"{BASE_URL}/exactmatch/ru/common/v4/search?appType=1&curr=rub&dest=-1257786&page=1&query={name}&regions=80,64,38,4,115,83,33,68,70,69,30,86,75,40,1,66,48,110,31,22,71,114&resultset=catalog&sort=popular&spp=0&suppressSpellcheck=false&xsubject={SubjectFiter.BOOKS.value};{SubjectFiter.SECONDHAND_BOOKS.value}"

        response = requests.get(
            request_url, headers=headers)

        if response.status_code != 200:
            raise Exception("Response status is not 200")

        to_return = []

        search_results = response.json()

        try:
            data = search_results['data']['products']
        except:
            return to_return

        for product in search_results['data']['products']:
            if len(to_return) == max_per_name:
                break

            id: int = product['id']

            card_url = Wildberries.get_card_url(id)

            response = requests.get(
                card_url, headers=headers
            )

            if response.status_code != 200:
                raise Exception("Response status is not 200")

            card = response.json()

            price = int(product['priceU'])/100
            book_name = card['imt_name']

            options: List[Dict[str, str]] = []
            try:
                options = card['options']
            except KeyError:
                to_return.append(Book('', book_name, 0, '', '', cover, price))
                continue

            options_mapped = {}
            for option in options:
                options_mapped[option['name']] = option['value']

            author = options_mapped.get("Автор", '')
            year = int(
                re.sub(r'[^0-9]', '', options_mapped.get("Год выпуска", '0')))
            description = card.get("description", 0)
            genre = options_mapped.get("Жанры/тематика", '')

            if not Wildberries.verify_name(name, book_name):
                continue

            to_return.append(Book(author, book_name, year,
                             description, genre, cover, price))

        return to_return
