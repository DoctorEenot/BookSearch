import logging
import time
import sys
import os
from .yandex_image_search import ImageSearcher

from .labirint import Labirint

import csv
from typing import List, Tuple
from .book import Book

from concurrent.futures import ThreadPoolExecutor, as_completed
import pathlib


def setup_logger(log_dir: str):

    try:
        os.mkdir(log_dir)
    except FileExistsError:
        pass

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(f"{log_dir}/{time.time()}.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )


def output_to_csv(books: List[Tuple[Book, Book]], file: str):
    with open(file, 'w') as csvfile:
        writer = csv.writer(csvfile)
        for book_set in books:
            for book in book_set:
                writer.writerow(book.to_row())
            writer.writerow([""])

    logging.info(f"File {file} created")


def read_names_from_csv(file: str) -> List[str]:
    book_names = []
    with open(file, 'r') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            book_names.append(row[0].strip(' '))
    return book_names


def get_all_books(books_names: List[Tuple[str, str]], covers: List[str]) -> List[List[Book]]:
    books = [[] for _ in range(len(books_names))]

    futures = {}
    index = 0
    with ThreadPoolExecutor(max_workers=20) as executor:
        # start threads
        for name1, name2 in books_names:
            cover = covers[index]
            if name1 != False:
                futures[executor.submit(
                    Labirint.search_book, name1, cover)] = index

            if name2 != False:
                futures[executor.submit(
                    Labirint.search_book, name2, cover)] = index

            index += 1

        for future in as_completed(futures):
            index = futures[future]
            try:
                data: List[Book] = future.result()
            except Exception as exc:
                logging.error("Error on a thread", exc_info=exc)
            else:
                if data is None:
                    continue
                for book in data:
                    books[index].append(book)

    return books


def main():
    logging.info("Starting an app")

    searcher = ImageSearcher(os.getenv("DRIVER_PATH"))

    books_names = []
    files: List[str] = []

    logging.info("Starting to search with covers")
    for file in os.listdir("./covers"):
        logging.debug(f"Starting a search for: {file}")
        books_names.append(searcher.search_image(f"./covers/{file}"))
        files.append(file)
    searcher.quit()
    logging.info(f"Went through {len(books_names)} covers in total")

    if pathlib.Path("books_to_search.csv").is_file():
        logging.info("Reading books_to_search.csv file")
        new_books = read_names_from_csv("books_to_search.csv")
        logging.info(f"Read {len(new_books)} books names in total")
        for book in new_books:
            books_names.append((book, False))
            files.append("")
    else:
        logging.warning(
            "File books_to_search.csv not found, skipping this stage")

    books = get_all_books(books_names, files)

    output_to_csv(books, "./books.csv")

    # logging.warning(
    #     "Please verify books, fix output and press enter to continue")
    # input()

    # logging.info("Last stage, creating items.csv file")

    logging.info("Program finished")
