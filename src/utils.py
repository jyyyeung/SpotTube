import re


def string_cleaner(input_string):
    """
    Cleans the input string to be used in the file name
    """
    raw_string = re.sub(r'[\/:*?"<>|]', " ", input_string)
    temp_string = re.sub(r"\s+", " ", raw_string)
    cleaned_string = temp_string.strip()
    return cleaned_string
