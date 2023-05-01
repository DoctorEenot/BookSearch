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
        return WebDriverWait(self.__browser, 15).until(
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

    def __deduct_book_name(self, items_orig: List[Tuple[str, str]]) -> str:
        '''
        items - titles, additional info of sites
        '''

        items = [list(filter(lambda string: string != '', re.sub(
            "[^\w\d]", ' ', item[0]).lower().split(' '))) for item in items_orig]

        additional_info = [list(filter(lambda string: string != '', re.sub(
            "[^\w\d]", ' ', item[1]).lower().split(' '))) for item in items_orig]

        for index, info in enumerate(additional_info):
            for word in info:
                if word not in items[index]:
                    items[index].append(word)

        key_words: Dict[str, KeyWord] = {}

        for sentence, item in enumerate(items):
            for index, word in enumerate(item):
                try:
                    key_words[word].found(index, sentence)
                except KeyError:
                    key_words[word] = KeyWord(index, sentence)

        most_used_words: List[Tuple[str, KeyWord]] = []

        part = len(items) / 2
        for word, data in key_words.items():
            if data.occurances > part:
                most_used_words.append((word, data))

        if len(most_used_words) == 0:
            return False

        most_used_words.sort(key=lambda word: min(
            word[1].indexes, key=word[1].indexes.get))

        # calculate average and average deviation
        sum_occurances = 0
        for most_used_word in most_used_words:
            sum_occurances += most_used_word[1].occurances

        average_occurance = sum_occurances / len(most_used_word)

        sum_deviations = 0
        for most_used_word in most_used_words:
            sum_deviations += (most_used_word[1].occurances -
                               average_occurance)**2

        average_deviation = math.sqrt(
            sum_deviations/len(most_used_word)) * 1.5

        # filter deviating words
        most_used_words = list(filter(
            lambda word: abs(word[1].occurances-average_occurance) <= average_deviation, most_used_words))

        # calculate collisions in same sentences
        graph = [[0]*len(most_used_words) for _ in range(len(most_used_words))]

        for index1, word1 in enumerate(most_used_words):
            for index2, word2 in enumerate(most_used_words):
                if index1 == index2:
                    continue

                for sentence in word1[1].sentences.keys():
                    if word2[1].sentences.get(sentence, False):
                        graph[index1][index2] += 1

        # average deviation of collisions
        collisions = [0]*len(most_used_words)
        for index1, line in enumerate(graph):
            for index2, collision in enumerate(line):
                collisions[index2] += collision

        sum_collisions = sum(collisions)
        average_collision = sum_collisions / len(collisions)

        sum_deviations = 0
        for collision in collisions:
            sum_deviations += (collision -
                               average_collision)**2

        average_deviation = math.sqrt(sum_deviations/len(collisions))*1.5

        to_return = []
        for index, collision in enumerate(collisions):
            if abs(collision-average_collision) <= average_deviation:
                to_return.append(most_used_words[index][0])

        # TODO: based on a graph place words correctly

        # post processing
        end_index = len(to_return)
        for i in range(end_index, -1, -1):
            end_index = i
            if i == 0:
                break
            if to_return[i-1] not in WORDS_TO_REMOVE:
                break

        start_index = 0
        for index, word in enumerate(to_return):
            start_index = index
            if word not in WORDS_TO_REMOVE:
                break

        to_return = to_return[start_index:end_index]

        if len(to_return) == 0:
            return False

        return " ".join(to_return)

    def __get_tags(self) -> List[str]:
        tags_parent: WebElement = WebDriverWait(self.__browser, 15).until(
            EC.presence_of_element_located(
                (By.XPATH,
                 '//section[@class="CbirSection CbirSection_decorated CbirTags"]')
            )
        )

        tags = tags_parent.find_elements(By.XPATH, './/a')
        return [tag.text for tag in tags]

    def search_image(self, image_path: str) -> Tuple[str, str]:
        self.__get_main_page()

        image_input = self.__get_image_input()

        try:
            image_input.send_keys(os.path.abspath(image_path))
        except Exception as e:
            logging.error(f"Error sending keys, error: {e}", exc_info=True)
            raise e

        tags = self.__get_tags()

        book_name_by_tags = tags[0]

        sites = self.__suggested_sites()
        self.__scroll_to_element(sites[-1])
        time.sleep(0.5)
        sites = self.__suggested_sites()
        self.__scroll_to_element(sites[-1])
        time.sleep(0.5)
        sites = self.__suggested_sites()
        self.__scroll_to_element(sites[-1])
        time.sleep(0.5)
        sites = self.__suggested_sites()

        items = [self.__extract_item_info(site) for site in sites]

        book_name_by_deduction = None
        if len(items) > 10:
            # items = items[:10]
            book_name_by_deduction = self.__deduct_book_name(
                [(item[1], "") for item in items])

            for i in [10, 5]:
                if not book_name_by_deduction:
                    items = items[:i]
                    book_name_by_deduction = self.__deduct_book_name(
                        [(item[1], item[2]) for item in items])
                else:
                    break
        else:
            book_name_by_deduction = self.__deduct_book_name(
                [(item[1], item[2]) for item in items])

        # print(book_name_by_tags, '|', book_name_by_deduction)

        return (book_name_by_tags, book_name_by_deduction)

    def quit(self):
        self.__browser.quit()
