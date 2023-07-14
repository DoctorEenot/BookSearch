from src.book import Book
import csv
from typing import List
import xlsxwriter

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

ABOUT_BEGINNING = 'Просим обратить внимание, что вы находитесь в разделе "букинистика". Состояние книги вы можете увидеть на фотографиях.'


def write_row(worksheet, row_num, row):
    for column, item in enumerate(row):
        worksheet.write(row_num, column, item)


def main():
    books: List[Book] = []
    with open("books.csv", 'r', encoding="utf-8-sig", newline=None) as csvfile:
        reader = csv.reader(csvfile)

        for row_num, row in enumerate(reader):
            if len(row) < 5:
                print("Not enough data in row: ", row_num)
                continue
            if row[0] == '' or row[1] == '':
                continue
            books.append(Book(*row))

    workbook = xlsxwriter.Workbook('items.xlsx')
    worksheet = workbook.add_worksheet()

    write_row(worksheet, 0, HEADER)

    for row_num, book in enumerate(books):
        row = ['',
               'Букинистические книги',
               '',
               'Мосчит',
               '',
               book.get_full_name(),
               '',
               '',
               book.price,
               '',
               ABOUT_BEGINNING+'\r\n'+book.description,
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

        write_row(worksheet, row_num+1, row)

    # with open("items.csv", 'w', encoding="utf-8-sig", newline='\n') as csvfile:
    #     writer = csv.writer(csvfile)
    #     writer.writerow(HEADER)

    #     for book in books:
    #         row = ['',
    #                'Букинистические книги',
    #                '',
    #                'Мосчит',
    #                '',
    #                book.get_full_name(),
    #                '',
    #                '',
    #                '1200',
    #                '',
    #                book.description,
    #                '4',
    #                '25',
    #                '15',
    #                book.author,
    #                'Хорошая',
    #                '400',
    #                '',
    #                book.year,
    #                book.genre,
    #                book.name,
    #                '',
    #                ''
    #                ]

    #         writer.writerow(row)

    workbook.close()


if __name__ == "__main__":
    main()
