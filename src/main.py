import ntpath
import logging
import time
import sys
import os
from .yandex_image_search import ImageSearcher
from PIL import Image, ExifTags
from .labirint import Labirint
from .wildberries import Wildberries
from .livelib import Livelib
import glob

import csv
from typing import List, Tuple
from .book import Book

from concurrent.futures import ThreadPoolExecutor, as_completed
import pathlib

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


def get_all_books(books_names: List[Tuple[str, str]], covers: List[str]) -> List[List[Book]]:
    books = [[] for _ in range(len(books_names))]
    futures = {}

    logging.info("Searching books on Labirint")
    not_found: int = 0
    not_found_indexes: List[Tuple[int, int]] = []
    with ThreadPoolExecutor(max_workers=4) as executor:
        # start threads
        for index, names in enumerate(books_names):
            cover = covers[index]
            for name_index, name in enumerate(names):
                futures[executor.submit(
                    Labirint.search_book, name, cover, 1)] = (index, name_index)

        for future in as_completed(futures):
            index, name_index = futures[future]
            try:
                data: List[Book] = future.result()
            except Exception as exc:
                not_found += 1
                logging.error("Error on a thread", exc_info=exc)
                not_found_indexes.append((index, name_index))
            else:
                if data is None or len(data) == 0:
                    not_found += 1
                    not_found_indexes.append((index, name_index))
                    continue
                for book in data:
                    books[index].append(book)

    if not_found == 0:
        return books

    logging.warning(f"Couldn't find {not_found} books on Labirint")

    logging.info("Searching books on Wildberries")

    futures = {}
    not_found = 0

    with ThreadPoolExecutor(max_workers=4) as executor:
        # start threads
        for index, name_index in not_found_indexes:
            cover = covers[index]
            futures[executor.submit(
                Wildberries.search_book, books_names[index][name_index], cover, 1)] = (index, name_index)

        not_found_indexes = []

        for future in as_completed(futures):
            index, name_index = futures[future]
            try:
                data: List[Book] = future.result()
            except Exception as exc:
                not_found += 1
                logging.error("Error on a thread", exc_info=exc)
            else:
                if data is None or len(data) == 0:
                    not_found += 1
                    not_found_indexes.append((index, name_index))
                    continue
                for book in data:
                    books[index].append(book)

    if not_found == 0:
        return books

    for index, name_index in not_found_indexes:
        if covers[index] != '':
            books[index].append(
                Book(covers[index], "NOT FOUND", 0, '', '', "", 0))
        else:
            books[index].append(
                Book(books_names[index][name_index], "NOT FOUND", 0, '', '', "", 0))

    logging.warning(f"Couldn't find {not_found} books on Wildberries")

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

        logging.info(f"Search by cover returned: {name1} | {name2}")

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
