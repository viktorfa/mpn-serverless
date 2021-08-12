from typing import List
import re
import logging
import pydash


dimension_pattern = (
    r"((?:\d+(?:,\d+)?)(?:\s*x\s*\d+(?:,\d+)?){1,2})"  # 30x40 or 40x40x0.5
)


def extract_dimensions(strings: List[str]):
    try:
        matches = pydash.flatten(
            list(
                re.findall(dimension_pattern, string.lower())
                for string in strings
                if string
            )
        )
        if len(matches) > 0:
            return re.sub(r"\s*", "", matches[0])
        else:
            return None
    except AttributeError as exc:
        logging.warning("" + str(exc) + "Could not extract number from: ")
        return None