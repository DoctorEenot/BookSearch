import ntpath
import logging
import time
import sys
import os
from .yandex_image_search import ImageSearcher
from PIL import Image
from .labirint import Labirint
from .wildberries import Wildberries
from .rusneb import RusNeb
# from .livelib import Livelib
import glob

import csv
from typing import List, Tuple, Dict
from .book import Book

from concurrent.futures import ThreadPoolExecutor, as_completed
import pathlib

# Tuple[engine, max_workers]
SEARCH_ENGINES = [
    (Labirint, 4),
    (Wildberries, 4),
    (RusNeb, 10)
]

COVERS_FOLDER = "./covers"

# https://www.bookvoed.ru/book?id=13196371#tdescription


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
    with open(file, 'w', encoding="utf-8-sig", newline='\n') as csvfile:
        writer = csv.writer(csvfile)
        for book_set in books:
            for book in book_set:
                writer.writerow(book.to_row())
            writer.writerow([""])

    logging.info(f"File {file} created")


def read_names_from_csv(file: str) -> List[str]:
    book_names = []
    with open(file, 'r', encoding="utf-8-sig", newline=None) as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            if len(row) == 0:
                continue
            book_names.append(row[0].strip(' '))
    return book_names


def get_all_books(books_names: List[List[str]], covers: List[str]) -> List[List[Book]]:
    global SEARCH_ENGINES

    books = [[] for _ in range(len(books_names))]

    # Dict[book_name, [cover_names,book_index]]
    book_name_covers_map: Dict[str, List[Tuple[str, int]]] = {}
    for book_index, names_cover in enumerate(zip(books_names, covers)):
        names, cover = names_cover
        for _, book_name in enumerate(names):

            book_data = book_name_covers_map.get(
                book_name, [])

            book_data.append((cover, book_index))

            book_name_covers_map[book_name] = book_data

    logging.info("Searching books in searching engines")

    logging.info(f"Total book names supplied: {len(book_name_covers_map)}")
    for engine, max_workers in SEARCH_ENGINES:
        futures = {}
        logging.info(f"Active engine: {engine.__name__}")
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            for book_name, mapped_covers in list(book_name_covers_map.items()):

                book_name_covers_map.pop(book_name)

                futures[executor.submit(
                        engine.search_book, book_name, '', 1)] = (book_name, mapped_covers)

            for future in as_completed(futures):
                book_name, mapped_covers = futures[future]

                try:
                    data: List[Book] = future.result()
                except Exception as exc:
                    logging.error("Error on a thread", exc_info=exc)
                    book_name_covers_map[book_name] = mapped_covers
                else:
                    if data is None or len(data) == 0:
                        book_name_covers_map[book_name] = mapped_covers
                        continue

                    for book in data:
                        for cover, book_index in mapped_covers:
                            book.cover = cover
                            books[book_index].append(book)

        logging.info(f"Books left: {len(book_name_covers_map)}")

    # not found
    for book_name, mapped_covers in list(book_name_covers_map.items()):
        for cover, book_index in mapped_covers:
            if cover != '':
                books[book_index].append(
                    Book(cover, "NOT FOUND", 0, '', '', "", 0))
            else:
                books[book_index].append(
                    Book(book_name, "NOT FOUND", 0, '', '', "", 0))

    logging.info(f"Not found total: {len(book_name_covers_map)}")

    return books


def prepare_covers():
    logging.info("Starting to preprocess covers")
    for file in os.listdir(COVERS_FOLDER):
        logging.debug(f"Staring to rotate: {file}")

        image = Image.open(COVERS_FOLDER+'/'+file)

        logging.debug("Saving file")

        image.save(COVERS_FOLDER+'/'+file)


def path_leaf(path):
    head, tail = ntpath.split(path)
    return tail or ntpath.basename(head)


def main():
    logging.info("Starting an app")

    # prepare_covers()

    # threads_pool = ThreadPoolExecutor(max_workers=4)
    # futures = {}

    searcher = ImageSearcher(os.getenv("DRIVER_PATH"))

    books_names = []
    files: List[str] = []

    files_index = 0

    logging.info("Starting to search with covers")
    for file in sorted(glob.glob(COVERS_FOLDER+'/*')):
        file = path_leaf(file)
        logging.info(f"Starting a search for: {file}")

        name1, name2 = searcher.search_image(f"./covers/{file}")

        logging.debug(f"Search by cover returned: {name1} | {name2}")

        name2, name3 = name2
        to_append = []

        if name1 != False:
            to_append.append(name1)

        if name2 != False:
            to_append.append(name2)

        if name3 != False:
            to_append.append(name3)

        if name1 and name2:
            to_append.append(name1+' '+name2)
            to_append.append(name2+' '+name1)

        if name2 and name3:
            # name2 + name3
            to_search = name2.split(" ")
            parts = name3.split(" ")
            if to_search[-1] == parts[0]:
                to_search = ' '.join(to_search[:-1])
            else:
                to_search = ' '.join(to_search)

            to_search = to_search + ' ' + name3
            to_append.append(to_search)

            # name3 + name2
            to_search = name3.split(" ")
            parts = name2.split(" ")
            if to_search[-1] == parts[0]:
                to_search = ' '.join(to_search[:-1])
            else:
                to_search = ' '.join(to_search)

            to_search = to_search + ' ' + name2
            to_append.append(to_search)

        to_append = list(set(to_append))  # remove duplicates

        files_index += 1
        books_names.append(to_append)

        files.append(file)
    searcher.quit()
    logging.info(f"Went through {files_index} covers in total")

    if pathlib.Path("books_to_search.csv").is_file():
        logging.info("Reading books_to_search.csv file")
        new_books = read_names_from_csv("books_to_search.csv")
        logging.info(f"Read {len(new_books)} books names in total")
        for book in new_books:
            books_names.append([book])
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
