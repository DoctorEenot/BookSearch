from typing import List
import re


class Book:
    author: str
    name: str
    year: int
    description: str
    genre: str
    cover: str
    price: int

    def __init__(self, author: str, name: str, year: int, description: str, genre: str, cover: str, price: int):
        self.author = author
        self.name = name
        try:
            self.year = int(year)
        except:
            self.year = int(re.sub(r'[^0-9]', '', year))
        self.description = description
        self.genre = genre
        self.cover = cover
        self.price = int(price)

    def get_full_name(self) -> str:
        return f"{self.author}: {self.name}"

    def to_row(self) -> List[str]:
        return [self.author, self.name, self.year, self.description, self.genre, self.cover, self.price]
