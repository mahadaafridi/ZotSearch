import json
import os
import re
from typing import List, Tuple, Dict, Set
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

# Gets the fields of all tokens
# Lowkey boof can prob simplify code
def get_token_fields(soup: BeautifulSoup, tokens: Set[str]) -> Dict[str, List[str]]:
    """
    Gets all the fields that is associated with the provided token.

    Args:
        soup (BeautifulSoup): parsed html using bs4
        token (Set[str]): set of tokens to be searched for
    
    Returns:
        Dict[str, List[str]]: dictionary containing all tokens as keys and their fields as values
    """
    token_fields = {}

    for token in tokens:
        fields = []

        # Find if token is in title field
        for title in soup.find_all('title'):
            if token in tokenize(title.get_text()):
                fields.append('title')
                break
        
        # Find if token in header field
        for header in soup.find_all(['h1', 'h2', 'h3']):
            if token in tokenize(header.get_text()):
                fields.append('header')
                break
        
        # Find if token in strong field
        for strong in soup.find_all('strong'):
            if token in tokenize(strong.get_text()):
                fields.append('strong')
                break
        
        # Find if token in body field
        for paragraph in soup.find_all(['p', 'span', 'div']):
            if token in tokenize(paragraph.get_text()):
                fields.append('body')
                break
        
        token_fields[token] = fields
    
    return token_fields