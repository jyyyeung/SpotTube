"""Utils for the application"""

import re

from stringpod import stringpod

from src.config import Config

config = Config()


def string_cleaner(input_string: str) -> str:
    """
    Cleans the input string to be used in the file name

    Examples:
        >>> string_cleaner("Hello World")
        "Hello World"
        >>> string_cleaner("Hello:*?<>| World")
        "Hello World"

    Args:
        input_string (str): The input string to clean

    Returns:
        str: The cleaned string
    """
    raw_string = re.sub(r'[\/:*?"<>|]', " ", input_string)
    temp_string = re.sub(r"\s+", " ", raw_string)
    cleaned_string = temp_string.strip()
    return cleaned_string


def contains_ignored_keywords(input_string: str, ignore_case: bool = True) -> bool:
    """
    Checks if the input string contains any of the ignored keywords

    Examples:
        >>> contains_ignored_keywords("Hello World")
        False
        >>> # If the ignored keywords are "伴奏", "純音樂", "配樂"
        >>> contains_ignored_keywords("Hello World伴奏")
        True

    Args:
        input_string (str): The input string to check

    Returns:
        bool: True if the input string contains any of the ignored keywords, False otherwise
    """
    return any(
        stringpod.contains_substring(input_string, keyword, ignore_case)
        for keyword in config.ignored_keywords
    )
