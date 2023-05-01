from src.book import Book
import csv
from typing import List

HEADER = ["Номер карточки",
          "Предмет",
          "Цвет",
          "Бренд",
          "Пол",
          "Название",
          "Артикул продавца",
          "Баркод товара",
          "Цена",
          "Состав",
          "Описание",
          "Высота упаковки",
          "Длина упаковки",
          "Ширина упаковки",
          "Автор",
          "Букинистическая сохранность",
          "Вес товара с упаковкой (г)",
          "Высота предмета",
          "Год выпуска",
          "Жанры/тематика",
          "Наименование книги",
          "Серия",
          "Медиафайлы"
          ]


def main():
    books: List[Book] = []
    with open("books.csv", 'r') as csvfile:
        reader = csv.reader(csvfile)

        for row_num, row in enumerate(reader):
            if len(row) < 5:
                print("Not enough data in row: ", row_num)
                continue
            books.append(Book(*row))

    with open("items.csv", 'w') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(HEADER)

        for book in books:
            row = ['',
                   'Букинистические книги',
                   '',
                   'Мосчит',
                   '',
                   book.get_full_name(),
                   '',
                   '',
                   '1200',
                   '',
                   book.description,
                   '4',
                   '25',
                   '15',
                   book.author,
                   'Хорошая',
                   '400',
                   '',
                   book.year,
                   book.genre,
                   book.name,
                   '',
                   ''
                   ]

            writer.writerow(row)


if __name__ == "__main__":
    main()
