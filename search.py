import json
import math
import os
import time
import mmap
from typing import List, Dict, Set, Tuple
from nltk.stem import PorterStemmer
from collections import defaultdict

def timer(func):
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        elapsed_ms = (end - start) * 1000
        print(f"{func.__name__} took {elapsed_ms:.2f} ms")
        return result
    return wrapper

class Search:
    def __init__(self, index_dir: str, doc_id_file: str):
        """
        Initialize the Search class with the split index files and document ID mapping.
        
        Args:
            index_dir (str): Directory containing the split index files
            doc_id_file (str): Path to the document ID mapping file
        """
        self.index_dir = index_dir
        self.doc_id_file = doc_id_file
        self.doc_id_map = {}      # Will store docid -> url mapping
        self.stemmer = PorterStemmer()
        self.total_docs = 0       # Will store total number of documents
        self.index_files = {}     # Will store mapping of ranges to file paths
        
        # Load document mapping and index files
        self._load_doc_id_map()
        self._load_index_files()

    def _load_index_files(self) -> None:
        """Load the mapping of letters to index files."""
        # Get all index files in the directory
        for filename in os.listdir(self.index_dir):
            if filename.endswith('.jsonl'):
                # Extract letter from filename (e.g., "a.jsonl" -> "a")
                letter = filename[:-6]  # Remove .jsonl
                self.index_files[letter] = os.path.join(self.index_dir, filename)

    def _get_index_file_for_token(self, token: str) -> str | None:
        """
        Get the appropriate index file for a given token.
        
        Args:
            token (str): The token to look up
            
        Returns:
            str | None: Path to the index file containing the token, or None if not found
        """
        if not token:
            return None
            
        first_char = token[0].lower()
        if first_char.isalpha():
            return self.index_files.get(first_char)
        return self.index_files.get('other')

    def _get_token_postings(self, token: str) -> List[Dict]:
        """
        Get postings for a specific token from the appropriate index file.
        
        Args:
            token (str): The token to look up
            
        Returns:
            List[Dict]: List of postings for the token
        """
        if not token:
            return []
            
        # Get the appropriate index file
        index_file = self._get_index_file_for_token(token)
        if not index_file:
            return []
            
        try:
            with open(index_file, 'r') as f:
                # Load File Content
                lines = f.readlines()

                # Binary Search for token
                left, right = 0, len(lines)-1
                while left <= right:
                    mid = left + ((right-left)//2)
                    data = json.loads(lines[mid])
                    current_token = data['token']
                    current_postings = data['postings']
                    
                    if current_token == token:
                        return current_postings
                    elif current_token < token:
                        left = mid+1
                    else:
                        right = mid-1
                        
        except Exception as e:
            print(f"Error looking up token {token}: {e}")
            
        return []

    def _load_doc_id_map(self) -> None:
        """Load the document ID to URL mapping."""
        try:
            with open(self.doc_id_file, 'r') as f:
                for line in f:
                    data = json.loads(line)
                    self.doc_id_map[data['docid']] = data['url']
            self.total_docs = len(self.doc_id_map)
        except Exception as e:
            print(f"Error loading document mapping: {e}")

    def tokenize_query(self, query: str) -> List[str]:
        """
        Tokenize and stem the query terms.
        
        Args:
            query (str): The search query
            
        Returns:
            List[str]: List of stemmed tokens
        """
        tokens = query.lower().split()
        return [self.stemmer.stem(token) for token in tokens]
    
    @timer
    def boolean_and_search(self, postings: Dict[str, List[Dict]]) -> Set[int]:
        """
        Perform boolean AND search for the given tokens.
        
        Args:
            postings (Dict[str, List[str]]): List of tokens to search for
            
        Returns:
            Set[int]: Set of document IDs that contain all tokens
        """
        if not postings:
            return set()
            
        #token postings
        token_postings = []
        for posting in postings.values(): # List[Dict] for All Tokens
            doc_ids = set()
            for p in posting: # Dict
                doc_ids.add(p['docid'])
            token_postings.append((len(doc_ids), doc_ids))
            
        #sort the tokens so that it is ordered from smallest to largest
        token_postings.sort(key=lambda x: x[0])
        
        #do intersections by smallest to largest to improve efficiency 
        result = token_postings[0][1]
        for _, doc_ids in token_postings[1:]:
            result = result.intersection(doc_ids)
            
        return result

    @timer
    def search(self, query: str) -> List[Dict]:
        """
        Search for documents matching the query and return ranked results.
        
        Args:
            query (str): Search query
            
        Returns:
            List[Dict]: List of ranked results with URLs and scores
        """
        tokens = self.tokenize_query(query)
        postings = {token: self._get_token_postings(token) for token in tokens}
        matching_docs = self.boolean_and_search(postings)
        
        results = []

        print(f'MATCHING DOCS: {len(matching_docs)}')
        for doc_id in matching_docs:
            score = 0 # Relevance score for doc

            for token in tokens:
                # Get tfidf score for this token and doc_id
                for posting in postings[token]:
                    if posting['docid'] == doc_id:
                        score += posting['tfidf']
                        break # No need to search rest of postings list

            results.append({
                'url': self.doc_id_map[doc_id],
                'score': score
            })
            
        results.sort(key=lambda x: x['score'], reverse=True)
        return results

    def run(self) -> None:
        """Runs the search"""
        while True:
            query = input("\nQuery: ").strip()
            if query.lower() == 'quit':
                break
                
            if not query:
                print("Please enter a valid query.")
                continue
                
            # Start timing
            start_time = time.time()
            results = search_engine.search(query)
            # Calculate elapsed time in milliseconds
            elapsed_time = (time.time() - start_time) * 1000
            
            if not results:
                print("No results found.")
            else:
                #top 5 results
                top_results = results[:5]
                with open('report.txt', 'a') as f:
                    f.write(f"Found {len(results)} results for \"{query}\" (showing top 5):\n")
                    for i, result in enumerate(top_results, 1):
                        f.write(f"{i}. {result['url']} (Score: {result['score']:.2f})\n")
                    f.write("\n")
                    
                print(f"\nFound {len(results)} results (showing top 5):")
                print(f"Query completed in {elapsed_time:.2f} milliseconds")
                for i, result in enumerate(top_results, 1):
                    print(f"{i}. {result['url']} (Score: {result['score']:.2f})")

if __name__ == '__main__':
    # Initialize search with the index directory and doc ID file
    search_engine = Search(
        index_dir="DEV_index",
        doc_id_file="DEV_doc_id.jsonl"
    )
    
    print("Welcome to the Search Engine!")
    print("Enter your query (type 'quit' to exit):")
    
    search_engine.run() 