import re


class SearchEngine:

    def verify_name(src: str, found: str) -> bool:
        src = list(filter(lambda el: el != '', re.sub(
            "[^\w\d]", ' ', src.lower()).split(" ")))
        found = list(filter(lambda el: el != '', re.sub(
            "[^\w\d]", ' ', found.lower()).split(" ")))

        collisions = 0

        for f in found:
            if f in src:
                collisions += 1

        if collisions / len(found) >= 0.90:
            return True

        return False
