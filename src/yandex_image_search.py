from selenium import webdriver
from selenium.webdriver import FirefoxOptions
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
import logging
from selenium.webdriver.remote.webelement import WebElement
import os
from typing import List, Tuple, Dict
import re
import time
import math
import numpy as np


class element_has_children_nodes(object):
    __children_locator: Tuple[By, str]
    __parent_node: WebElement

    def __init__(self, locator: Tuple[By, str], parent_node: WebElement):
        self.__children_locator = locator
        self.__parent_node = parent_node

    def __call__(self, _):
        elements = self.__parent_node.find_elements(*self.__children_locator)
        if len(elements) == 0:
            return False
        return elements


WORDS_TO_REMOVE = ["wildberries", 'в', "на",
                   'купить', 'и', 'авито', 'объявления']


class KeyWord:
    occurances: int
    indexes: Dict[int, int]
    sentences: Dict[int, bool]

    def __init__(self, index: int, sentence: int):
        self.occurances = 1
        self.indexes = dict()
        self.sentences = dict()
        self.indexes[index] = 1
        self.sentences[sentence] = True

    def found(self, index: int, sentence: int):
        self.occurances += 1
        try:
            self.indexes[index] += 1
        except KeyError:
            self.indexes[index] = 1

        self.sentences[sentence] = True


class ImageSearcher:
    __browser = None

    def __init__(self, driver_path: str):
        firefox_options = FirefoxOptions()
        firefox_options.add_argument("--profile-root")
        firefox_options.add_argument("./driver_profile/")
        firefox_options.add_argument("-profile")
        firefox_options.add_argument("./driver_profile/")
        self.__browser = webdriver.Firefox(
            executable_path=driver_path, options=firefox_options)

    def __get_image_input(self) -> WebElement:
        try:
            return WebDriverWait(self.__browser, 30).until(
                EC.presence_of_element_located(
                    (By.XPATH, '//input[@accept="image/*"]'))
            )
        except:
            self.__browser.refresh()
            return WebDriverWait(self.__browser, 30).until(
                EC.presence_of_element_located(
                    (By.XPATH, '//input[@accept="image/*"]'))
            )

    def __suggested_sites(self) -> List[WebElement]:
        sites: WebElement = WebDriverWait(self.__browser, 15).until(
            EC.presence_of_element_located(
                (By.XPATH, '//ul[@class="CbirSites-Items"]')
            )
        )
        return WebDriverWait(self.__browser, 15).until(
            element_has_children_nodes(
                (By.XPATH, './/li[@class="CbirSites-Item"]'), sites)
        )

    def __extract_item_info(self, item: WebElement) -> Tuple[str, str, str]:
        '''
        returns (url, title, additional info)
        '''

        title: WebElement = item.find_element(
            By.XPATH, './/div[@class="CbirSites-ItemTitle"]')

        link: WebElement = title.find_element(By.XPATH, './/a')

        additional_info: WebElement = item.find_element(
            By.XPATH, './/div[@class="CbirSites-ItemDescription"]')

        return (link.get_attribute("href"), title.text, additional_info.text)

    def __get_main_page(self, url="https://yandex.com/images/"):
        self.__browser.get(url)

    def __scroll_to_element(self, element: WebElement):
        self.__browser.execute_script(
            "arguments[0].scrollIntoView();", element)

    def __deduct_book_name(self, items_orig: List[Tuple[str, str]]) -> Tuple[str, str]:
        '''
        items - titles, additional info of sites
        '''

        items = [list(filter(lambda string: string != '', re.sub(
            "[^\w\d]", ' ', item[0]).lower().split(' '))) for item in items_orig]

        additional_info = [list(filter(lambda string: string != '', re.sub(
            "[^\w\d]", ' ', item[1]).lower().split(' '))) for item in items_orig]

        items = items + additional_info

        key_words: Dict[str, int] = {}

        for words in items:
            for word in words:
                try:
                    key_words[word] += 1
                except KeyError:
                    key_words[word] = 0

        graph_labels = list(key_words.keys())
        graph = [[0]*len(graph_labels) for _ in range(len(graph_labels))]
        graph = np.array(graph, dtype=np.uint32)

        enumerated_labels: Dict[str, int] = {}
        for index, label in enumerate(graph_labels):
            enumerated_labels[label] = index

        for sentence in items:
            for first, second in zip(sentence, sentence[1:]):
                first_index = enumerated_labels[first]
                second_index = enumerated_labels[second]
                graph[first_index][second_index] += 1

        paths: Dict[Tuple[List[int], int]] = []
        visited_nodes: Dict[int, bool] = {}
        for row_index, row in enumerate(graph):
            if visited_nodes.get(row_index, False):
                continue

            visited_nodes[row_index] = True
            path = [row_index]
            max_value = row.max()
            if max_value > 0:
                while True:
                    row_index = np.argmax(row)
                    row = graph[row_index]
                    path.append(row_index)

                    if visited_nodes.get(row_index, False) or row.max() != max_value:
                        break

                    visited_nodes[row_index] = True

            paths.append((path, max_value))

        phrases: List[List[str]] = []

        largest_value: int = -1
        largest_index: int = -1

        second_largest_value: int = -1
        second_largest_index: int = -1

        for index, data in enumerate(paths):
            path, value = data

            phrases.append([graph_labels[index] for index in path])

            if value > largest_value:
                second_largest_value = largest_value
                second_largest_index = largest_index

                largest_value = value
                largest_index = index
            elif value > second_largest_value or value == largest_value:
                second_largest_value = value
                second_largest_index = index

        if len(phrases) == 0:
            return False

        to_return = []
        to_return.append(phrases[largest_index])
        if second_largest_value > -1:
            to_return.append(phrases[second_largest_index])
        if len(phrases) == 1:
            return (' '.join(to_return[0]), False)

        return (' '.join(to_return[0]), ' '.join(to_return[1]))

    def __get_tags(self) -> List[str]:
        try:
            tags_parent: WebElement = WebDriverWait(self.__browser, 30).until(
                EC.presence_of_element_located(
                    (By.XPATH,
                     '//section[@class="CbirSection CbirSection_decorated CbirTags"]')
                )
            )
        except:
            logging.warning(f"Couldn't find tags for an image")
            return []

        tags = tags_parent.find_elements(By.XPATH, './/a')
        return [tag.text for tag in tags]

    def __incorrect_file_input(self) -> bool:
        try:
            panel: WebElement = WebDriverWait(self.__browser, 4, poll_frequency=0.1).until(
                EC.presence_of_element_located(
                    (By.XPATH,
                     "//div[contains(concat(' ', normalize-space(@class), ' '), ' CbirUploadErrorNotify ')]")
                )
            )
            return True
        except Exception as e:
            return False

    def __detect_suggested_sites(self) -> bool:
        try:
            WebDriverWait(self.__browser, 15).until(
                EC.presence_of_element_located(
                    (By.XPATH, '//ul[@class="CbirSites-Items"]')
                )
            )
            return True
        except:
            return False

    def search_image(self, image_path: str) -> Tuple[str, str]:
        self.__get_main_page()

        time.sleep(0.5)

        image_input = self.__get_image_input()

        while True:
            try:
                image_input.send_keys(os.path.abspath(image_path))
            except Exception as e:
                logging.error(f"Error sending keys, error: {e}", exc_info=True)
                raise e

            # if self.__incorrect_file_input():
            #     logging.warning(
            #         f"Browser returned 'Incorrect format' for image: {image_path}")
            #     logging.warning(f"Retrying image search")
            # else:
            #     break

            if self.__detect_suggested_sites():
                break

        tags = self.__get_tags()

        book_name_by_tags = False
        if len(tags) > 0:
            book_name_by_tags = tags[0]

        sites = self.__suggested_sites()
        self.__scroll_to_element(sites[-1])
        time.sleep(0.5)
        sites = self.__suggested_sites()
        # self.__scroll_to_element(sites[-1])
        # time.sleep(0.5)
        # sites = self.__suggested_sites()
        # self.__scroll_to_element(sites[-1])
        # time.sleep(0.5)
        # sites = self.__suggested_sites()

        items = [self.__extract_item_info(site) for site in sites]

        book_names_by_deduction = self.__deduct_book_name(
            [(item[1], item[2]) for item in items])

        return (book_name_by_tags, book_names_by_deduction)

    def quit(self):
        self.__browser.quit()

    def __del__(self):
        return
        self.quit()
