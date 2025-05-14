import json
import os
import re
from typing import List, Tuple, Dict
from bs4 import BeautifulSoup
from Posting import Posting

# Tokenizes content
def tokenize(content: str) -> List[str]:
    """
    Tokenizes the provided content into alphanumeric sequences and returns as a list.

    Args:
        content (str): Input string to be tokenized
    
    Returns:
        List[str]: A list of tokens
    """
    tokens = re.findall(r'[a-z0-9]+', content.lower())

    return tokens

# Computes frequency of tokens
def token_frequency(tokens: List[str]) -> Dict[str, int]:
    """
    Returns the frequency of each token in the provided list as a dictionary.

    Args:
        tokens (List[str]): list of tokens
    
    Returns:
        Dict[str, int]: dictionary with token (str) as key and frequency (int) as value
    """
    frequencies = dict()

    for token in tokens:
        if token in frequencies:
            frequencies[token] += 1
        else:
            frequencies[token] = 1
    
    return frequencies

# Gets URL, content, and encoding of webpage
def get_info(file_path: str) -> Tuple[str]:
    """
    Given a file path to a .json file, returns the URL, content, and encoding of the webpage.

    Args:
        file_path (str): Relative file path to .json file
    
    returns:
        Tuple[str]: URL, content, and encoding of webpage
    """
    with open(file_path, 'r') as file:
        data = json.load(file)

    return (data['url'], data['content'], data['encoding'])