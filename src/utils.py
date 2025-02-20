import re


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
