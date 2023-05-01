from typing import List


class Book:
    author: str
    name: str
    year: int
    description: str
    genre: str
    cover: str

    def __init__(self, author: str, name: str, year: int, description: str, genre: str, cover: str = ""):
        self.author = author
        self.name = name
        self.year = int(year)
        self.description = description
        self.genre = genre
        self.cover = cover

    def get_full_name(self) -> str:
        return f"{self.author}: {self.name}"

    def to_row(self) -> List[str]:
        return [self.author, self.name, self.year, self.description, self.genre, self.cover]
