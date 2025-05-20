import sys
import json
import os
import re
from typing import List, Tuple, Dict, Set
from bs4 import BeautifulSoup
from Posting import Posting
from urllib.parse import urldefrag
import logging
import heapq
from pympler import asizeof
from nltk.stem import PorterStemmer
FOLDER_DIR = "small_dev"

def custom_hash(s):
    """
    Took this from Geeks for Geeks since we aren't allowed to use a library for the hashing
    """
    n = len(s)
    p = 31
    m = int(1e9 + 7)
    hashVal = 0
    pPow = 1
    for i in range(n):
        hashVal = (hashVal + (ord(s[i]) - ord('a') + 1) * pPow) % m
        pPow = (pPow * p) % m
    return hashVal

class InvertedIndex:
    # directorys
    PARTIAL_INDEX_DIR = "small_dev_partial"
    FINAL_INDEX_FILE = "small_dev_index.jsonl"
    LOG_FILE = "small_dev.log"
    DOC_ID_FILE = "small_dev_doc_id"
    
    def __init__(self):
        self.DOC_ID_COUNT = 1 # tracks the document id
        self.DOC_ID = dict() # map of doc_id ot url
        self.THRESHOLD_SIZE = 20_000_000 # 20MB threshold
        self.partial_index = dict() #stores partial index in memory
        self.partial_index_file_count = 0 #counts the number of partial index files in total
        self.stemmer = PorterStemmer()
        self.final_index = dict()
        self.near_duplicate = set() # store fingerprints 

        #makes the folder where we store the partial index
        if not os.path.exists(self.PARTIAL_INDEX_DIR):
            os.makedirs(self.PARTIAL_INDEX_DIR)
            
        #initialize logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.LOG_FILE),
                logging.StreamHandler()
            ]
        )
        logging.info("initialized the directory")

    def tokenize(self, content: str) -> List[str]:
        """
        Tokenizes the provided content into alphanumeric sequences and returns as a list.
        Numbers are preserved as-is, while words are stemmed.

        Args:
            content (str): Input string to be tokenized
        
        Returns:
            List[str]: A list of tokens
        """
        # First split into words and numbers
        tokens = re.findall(r'[a-z0-9]+', content.lower())
        
        # Process each token
        processed_tokens = []
        for token in tokens:
            if token.isdigit():
                # Keep numbers as-is
                processed_tokens.append(token)
            else:
                # Stem only words
                processed_tokens.append(self.stemmer.stem(token))
        
        return processed_tokens

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

    def get_info(self, file_path: str) -> Tuple[str, str, str]:
        """
        Given a file path to a .json file, returns the URL, content, and encoding of the webpage.

        Args:
            file_path (str): Relative file path to .json file
        
        returns:
            Tuple[str]: URL, content, and encoding of webpage
        """
        try:
            with open(file_path, 'r') as file:
                data = json.load(file)
            return (data['url'], data['content'], data['encoding'])
        except json.JSONDecodeError as e:
            logging.info(f"JSON decoding error with file {file_path}: {e}")
            return ("", "", "")
        except Exception as e:
            logging.info(f"Failed to process file {file_path}: {e}")
            return ("", "", "")


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

        # pre tokenize everything to be more efficient
        title_text = ' '.join(title.get_text() for title in soup.find_all('title'))
        header_text = ' '.join(header.get_text() for header in soup.find_all(['h1', 'h2', 'h3']))
        strong_text = ' '.join(strong.get_text() for strong in soup.find_all('strong'))
        body_text = ' '.join(p.get_text() for p in soup.find_all(['p', 'span', 'div']))

        title_tokens = set(self.tokenize(title_text))
        header_tokens = set(self.tokenize(header_text))
        strong_tokens = set(self.tokenize(strong_text))
        body_tokens = set(self.tokenize(body_text))

        for token in tokens:
            fields = []
            if token in title_tokens:
                fields.append('title')
            if token in header_tokens:
                fields.append('header')
            if token in strong_tokens:
                fields.append('strong')
            if token in body_tokens:
                fields.append('body')
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
        docid = self.DOC_ID_COUNT
        self.DOC_ID[docid] = defragmented_url # Map url to docid
        self.DOC_ID_COUNT += 1
        return docid

    def docid_to_url(self, docid: int) -> str:
        """
        Returns the url associated with the provided docid

        Args:
            docid (int): docid

        Returns:
            str: URL associated with docid
        """
        return self.DOC_ID.get(docid, "")
    
    def is_duplicate(self, tokens: List[str]) -> bool:
        """
        Checks if a document is a near-duplicate of any previously processed document.
        
        Args:
            tokens (List[str]): List of tokens from the document
            
        Returns:
            bool: True if document is a duplicate, False otherwise
        """
        similarity_treshold = 0.85
        min_token_count = 10
        
        if len(tokens) < min_token_count:
            return False
        
        trigrams = []
        for i in range(len(tokens) - 2):
            trigram = ' '.join(tokens[i:i + 3])
            trigrams.append(trigram)

        trigram_hashes = set()
        for ngram in trigrams:
            trigram_hashes.add(custom_hash(ngram))

        selected_hashes = set()
        for h in trigram_hashes:
            if h % 4 == 0:
                selected_hashes.add(h)

        for fingerprint in self.near_duplicate:
            intersection = selected_hashes.intersection(fingerprint)
            union = selected_hashes.union(fingerprint)
            if union:
                similarity_score = len(intersection) / len(union)
            else:
                similarity_score = 0.0
            if similarity_score >= similarity_treshold:
                return True

        self.near_duplicate.add(frozenset(selected_hashes))    
        return False

    def process_document(self, file_path: str) -> None:
        """
        Processes the provided document into an inverted index.

        Args:
            file_path (str): relative file path to document
        
        Returns:
            None
        """
        url, content, encoding = self.get_info(file_path) # Get info

        if not url or not content:  # Skip if we couldn't get valid content
            return

        try:
            soup = BeautifulSoup(content, 'html.parser')
            content = soup.get_text(separator=' ', strip=True)
            tokens = self.tokenize(content)
            
            # Check for duplicates before processing
            if self.is_duplicate(tokens):
                logging.info(f"Skipping dupe document{url}")
                return
                
            docid = self.url_to_docid(url)
            tf = self.token_frequency(tokens)
            fields = self.get_token_fields(soup, set(tokens))

            # Create inverted index for document
            for token, frequency in tf.items():
                posting = Posting(docid, frequency, fields[token])
                if token in self.partial_index:
                    self.partial_index[token].append(posting)
                else:
                    self.partial_index[token] = [posting]
                    
        except Exception as e:
            logging.error(f"Error processing document {file_path}: {e}")

    
    # These functions will be for merging and dumping partial index
    def dump_partial_index(self) -> None:
        """
        Dumps partial index info to a .json file and resets in-memory index to reduce memory usage.

        Returns:
            None
        """
        file_name = f'{self.PARTIAL_INDEX_DIR}/{self.partial_index_file_count}.jsonl'

        # i did this because you can't json dumps a class that we created (the Postings class)
        # pretty inefficient, so i may consider just getting rid of the posting class so we dont gotta do this part
        serializable_data = {
            token: [posting.posting_data for posting in postings]
            for token, postings in sorted(self.partial_index.items())
        }

        with open(file_name, 'w') as f:
            for token, postings in serializable_data.items():
                json_line = json.dumps({token: postings})
                f.write(json_line + '\n')

        self.partial_index_file_count += 1
        self.partial_index.clear()
        self.near_duplicate.clear() #clear the fingerprints also so it doens't overflow

    def check_and_dump(self) -> None:
        """
        If size of partial index exceeds threshold, dump and clear it.
        
        Returns:
            None
        """
        size_in_bytes = asizeof.asizeof(self.partial_index)        
        logging.info(f"SIZE IN BYTES: {size_in_bytes}")

        #CHANGE FOR ACTUAL IMPLEMENTATION
        if size_in_bytes > self.THRESHOLD_SIZE:
            self.dump_partial_index()

            logging.info("DUMPED THE FILE")
    
    def save_doc_id_mapping(self) -> None:
        """
        Saves the docID
        """
        with open(self.DOC_ID_FILE, 'w') as f:
            for docid, url in sorted(self.DOC_ID.items()):
                json_line = json.dumps({"docid": docid, "url": url})
                f.write(json_line + '\n')
        logging.info(f"Saved DOC_ID mapping") 

    """
    Currently this stores the entire final index in-memory which defeats the purpose of the partial indexes
    Need to do a multi-way merge. 
        Open and read all files simultaneously line by line. 

        Since sorted alphabetically we can do a min heap. 

        Grab one token from each file, whichever token is the lowest alpahbetically, merge it with all
        other instances then add to final index. 
        
    """
    def merge_partial_indexes(self) -> None:
        """
        Merges all partial indexes into a final inverted index.

        Returns:
            None
        """
        # List of open file descriptors
        logging.info("STARTING MERGE")
        files = [open(f'{self.PARTIAL_INDEX_DIR}/{i}.jsonl', 'r') for i in range(self.partial_index_file_count)]

        def read_next(file):
            line = file.readline()
            if not line:
                return None
            return json.loads(line)

        # Initialize min-heap with first line of each file
        heap = []
        for i, f in enumerate(files):
            entry = read_next(f)
            if entry:
                key = list(entry.keys())[0]
                heapq.heappush(heap, (key, i, entry[key]))

        # Open final inverted index file and dump to it
        with open(self.FINAL_INDEX_FILE, 'w') as out_file:
            current_token = None
            current_postings = []
            posting_map = {}  # Map to track unique docids and their frequencies

            while heap:
                token, file_idx, postings = heapq.heappop(heap)

                # No more of same token in heap, merge and dump to final index
                if token != current_token:
                    if current_token is not None:
                        # Convert posting map back to list and sort by docid
                        merged_postings = [
                            {"docid": docid, "tf": data["tf"], "fields": data["fields"]}
                            for docid, data in sorted(posting_map.items())
                        ]
                        out_file.write(json.dumps({'token': current_token, 'postings': merged_postings}) + '\n')
                    current_token = token
                    posting_map = {}
                    # Initialize posting map with current postings
                    for posting in postings:
                        docid = posting["docid"]
                        if docid in posting_map:
                            posting_map[docid]["tf"] += posting["tf"]
                            posting_map[docid]["fields"] = list(set(posting_map[docid]["fields"] + posting["fields"]))
                        else:
                            posting_map[docid] = {"tf": posting["tf"], "fields": posting["fields"]}
                else:
                    # Same token from multiple files, merge postings
                    for posting in postings:
                        docid = posting["docid"]
                        if docid in posting_map:
                            posting_map[docid]["tf"] += posting["tf"]
                            posting_map[docid]["fields"] = list(set(posting_map[docid]["fields"] + posting["fields"]))
                        else:
                            posting_map[docid] = {"tf": posting["tf"], "fields": posting["fields"]}

                # Get next line from file
                next_entry = read_next(files[file_idx])
                if next_entry:
                    key = list(next_entry.keys())[0]
                    heapq.heappush(heap, (key, file_idx, next_entry[key]))
            
            #write the last token 
            if current_token is not None:
                merged_postings = [
                    {"docid": docid, "tf": data["tf"], "fields": data["fields"]}
                    for docid, data in sorted(posting_map.items())
                ]
                out_file.write(json.dumps({'token': current_token, 'postings': merged_postings}) + '\n')
            
            logging.info("FINAL MERGE")

        logging.info("SAVE MAPPING")
        self.save_doc_id_mapping()

if __name__ == '__main__':
    inverted_index_instance = InvertedIndex()
    
    for folder in os.listdir(FOLDER_DIR):
        logging.info(f"ON FOLDER {folder}")
        folder_path = os.path.join(FOLDER_DIR, folder)  
        print(folder_path)
        for file in os.listdir(folder_path):
            logging.info(f"ON FILE{file}")
            file_path = os.path.join(folder_path, file)
            inverted_index_instance.process_document(file_path)
            inverted_index_instance.check_and_dump()
    

    if inverted_index_instance.partial_index:
        inverted_index_instance.dump_partial_index()
    
    inverted_index_instance.merge_partial_indexes()
