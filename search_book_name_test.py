from src.yandex_image_search import ImageSearcher
import os
from src.main import COVERS_FOLDER, path_leaf
import glob
from dotenv import load_dotenv


def main():
    load_dotenv()
    searcher = ImageSearcher(os.getenv("DRIVER_PATH"))

    for file in sorted(glob.glob(COVERS_FOLDER+'/*')):
        file = path_leaf(file)

        name1, name2 = searcher.search_image(f"./covers/{file}")

        name2, name3 = name2

        print(f"{name1} | {name2} | {name3}")


if __name__ == "__main__":
    main()
