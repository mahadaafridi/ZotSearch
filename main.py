import sys
import json
import os
import re
from typing import List, Tuple, Dict, Set
from bs4 import BeautifulSoup
from Posting import Posting
from urllib.parse import urldefrag
import logging

class InvertedIndex:
    def __init__(self):
        self.DOC_ID_COUNT = 1 # Keeps track of docid number
        self.DOC_ID = dict() # Maps docid to URL
        self.THRESHOLD_SIZE = 10_000_000 # 10MB threshold
        self.partial_index = dict()
        self.partial_index_file_count = 0 #counts the number of partial index files in total

        self.final_index = dict()
        #makes the folder where we store the partial index
        if not os.path.exists("partial_index"):
            os.makedirs("partial_index")
            
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler("inverted_index.log"),
                logging.StreamHandler()
            ]
        )
        logging.info("initialized the directory")

    def tokenize(self, content: str) -> List[str]:
        """
        Tokenizes the provided content into alphanumeric sequences and returns as a list.

        Args:
            content (str): Input string to be tokenized
        
        Returns:
            List[str]: A list of tokens
        """
        tokens = re.findall(r'[a-z0-9]+', content.lower())

        return tokens

    def token_frequency(self, tokens: List[str]) -> Dict[str, int]:
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

    def get_info(self, file_path: str) -> Tuple[str]:
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
    def get_token_fields(self, soup: BeautifulSoup, tokens: Set[str]) -> Dict[str, List[str]]:
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
                if token in self.tokenize(title.get_text()):
                    fields.append('title')
                    break
            
            # Find if token in header field
            for header in soup.find_all(['h1', 'h2', 'h3']):
                if token in self.tokenize(header.get_text()):
                    fields.append('header')
                    break
            
            # Find if token in strong field
            for strong in soup.find_all('strong'):
                if token in self.tokenize(strong.get_text()):
                    fields.append('strong')
                    break
            
            # Find if token in body field
            # If the field so far is empty then check all divs, if not empty only check in relevant <p> and <span> tags
            if not fields: # If fields empty
                for paragraph in soup.find_all(['p', 'span', 'div']):
                    if token in self.tokenize(paragraph.get_text()):
                        fields.append('body')
                        break
            else:
                for paragraph in soup.find_all(['p', 'span']):
                    if token in self.tokenize(paragraph.get_text()):
                        fields.append('body')
                        break
            
            token_fields[token] = fields
        
        return token_fields

    def url_to_docid(self, url: str) -> int:
        """
        Maps a docid to the provided url and returns it.

        Args:
            url (str): URL string to be mapped
        
        Returns:
            int: docid for URL
        """

        defragmented_url = urldefrag(url)[0] # Defrag url
        self.DOC_ID[self.DOC_ID_COUNT] = defragmented_url # Map url to docid
        self.DOC_ID_COUNT += 1

        return self.DOC_ID_COUNT - 1 #changed this because this funciton is supposed to return an int (before the variable it was returning was a dict)

    def docid_to_url(self, docid: int) -> str:
        """
        Returns the url associated with the provided docid

        Args:
            docid (int): docid

        Returns:
            str: URL associated with docid
        """
        return self.DOC_ID.get(docid, "")
    
    def process_document(self, file_path: str) -> None:
        """
        Processes the provided document into an inverted index.

        Args:
            file_path (str): relative file path to document
        
        Returns:
            None
        """
        url, content, encoding = self.get_info(file_path) # Get info
        soup = BeautifulSoup(content, 'html.parser') # Parse
        content = soup.get_text(separator=' ', strip=True) # Get relevant text
        tokens = self.tokenize(content) # Tokenize
        docid = self.url_to_docid(url) # Get docid
        tf = self.token_frequency(tokens) # Get token frequencies
        fields = self.get_token_fields(soup, set(tokens)) # Get token fields

        # Create inverted index for document
        for token, frequency in tf.items():
            posting = Posting(docid, frequency, fields[token])
            if token in self.partial_index:
                self.partial_index[token].append(posting)
            else:
                self.partial_index[token] = [posting]

    def print_index(self) -> None:
        """
        Prints out partial inverted index to the terminal.

        Returns:
            None
        """
        for key, value in self.partial_index.items():
            print(f"{key}")
            print(f"    docid: {value[0].docid}")
            print(f"    frequency: {value[0].tf}")
            print(f"    fields: {value[0].fields}\n")
    
    # These functions will be for merging and dumping partial index
    def dump_partial_index(self) -> None:
        """
        Dumps partial index info to a .json file and resets in-memory index to reduce memory usage.

        Returns:
            None
        """
        file_name = f'partial_index/{self.partial_index_file_count}.json'

        # i did this because you can't json dumps a class that we created (the Postings class)
        # pretty inefficient, so i may consider just getting rid of the posting class so we dont gotta do this part
        seriazable_data = {
            token: [posting.posting_data for posting in postings]
            for token, postings in sorted(self.partial_index.items())
        }

        with open(file_name, 'w') as f:
            json.dump(seriazable_data, f)
        
        self.partial_index_file_count += 1
        self.partial_index.clear()

    def check_and_dump(self) -> None:
        """
        If size of partial index exceeds threshold, dump and clear it.
        
        Returns:
            None
        """
        size_in_bytes = sys.getsizeof(self.partial_index)

        #CHANGE FOR ACTUAL IMPLEMENTATION
        if size_in_bytes > self.THRESHOLD_SIZE:
            self.dump_partial_index()
            logging.debug("DUMPED THE FILE")
    
    """
    Currently this stores the entire final index in-memory which defeats the purpose of the partial indexes
    Need to do a multi-way merge. 
        Open and read all files simultaneously line by line. 

        Since sorted alphabetically we can do a min heap. 

        Grab one token from each file, whichever token is the lowest alpahbetically, merge it with all
        other instances then add to final index. 
        
        Repeat this over and over until done merging type shi
    """
    def merge_partial_indexes(self) -> None:
        """
        Merges all partial indexes into a final inverted index.

        Returns:
            None
        """
        for file_name in os.listdir("partial_index"):
            file_name = os.path.join("partial_index", file_name) 
            with open(file_name, 'r') as f:
                partial_index = json.load(f)
                # Merge the partial index into the final index
                for token, postings in partial_index.items():
                    if token not in self.final_index:
                        self.final_index[token] = []
                    self.final_index[token].extend(postings)

        # Save the merged final index and print metrics
        with open("final_index.json", 'w') as f:
            json.dump(self.final_index, f)
        print(f"unique tokens: {len(self.final_index)}")
        print(f"num of docs: {self.DOC_ID_COUNT - 1}")

if __name__ == '__main__':
    inverted_index_instance = InvertedIndex()
    folder_dir = "DEV"
    for folder in os.listdir(folder_dir):
        logging.info(f"ON FOLDER {folder}")
        folder_path = os.path.join(folder_dir, folder)  
        for file in os.listdir(folder_path):
            logging.info(f"ON FILE{file}")
            file_path = os.path.join(folder_path, file)
            inverted_index_instance.process_document(file_path)
            inverted_index_instance.check_and_dump()
    
    inverted_index_instance.merge_partial_indexes()
