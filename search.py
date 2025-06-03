import json
import math
import os
import time
import mmap
from typing import List, Dict, Set, Tuple
from nltk.stem import PorterStemmer
from collections import defaultdict
import concurrent.futures

STOP_WORDS = {"a","about","above","after","again","against","all","am",
            "an","and","any","are","aren't","as","at","be","because","been",
            "before","being","below","between","both","but","by","can't",
            "cannot","could","couldn't","did","didn't","do","does","doesn't",
            "doing","don't","down","during","each","few","for","from","further",
            "had","hadn't","has","hasn't","have","haven't","having","he","he'd",
            "he'll","he's","her","here","here's","hers","herself","him","himself",
            "his","how","how's","i","i'd","i'll","i'm","i've","if","in","into","is",
            "isn't","it","it's","its","itself","let's","me","more","most","mustn't",
            "my","myself","no","nor","not","of","off","on","once","only","or","other",
            "ought","our","ours	ourselves","out","over","own","same","shan't","she",
            "she'd","she'll","she's","should","shouldn't","so","some","such","than",
            "that","that's","the","their","theirs","them","themselves","then","there",
            "there's","these","they","they'd","they'll","they're","they've","this","those",
            "through","to","too","under","until","up","very","was","wasn't","we","we'd",
            "we'll","we're","we've","were","weren't","what","what's","when","when's","where",
            "where's","which","while","who","who's","whom","why","why's","with","won't","would",
            "wouldn't","you","you'd","you'll","you're","you've","your","yours","yourself","yourselves"}


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

    @timer
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
        tokens = set(query.lower().split())
        tokens = tokens - STOP_WORDS
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
        visited_urls = set()
        
        for doc_id in matching_docs:
            score = 0 # Relevance score for doc

            for token in tokens:
                # Binary search for doc tfidf
                postings_list = postings[token]
                left, right = 0, len(postings_list)-1

                while left <= right:
                    mid = left + ((right-left) // 2)
                    current_docid = postings_list[mid]['docid']

                    if current_docid == doc_id:
                        score += postings_list[mid]['tfidf']
                        break # Found docid no need to continue search
                    elif current_docid < doc_id:
                        left = mid+1 # Search right half
                    else:
                        right = mid-1 # Search left half

            url = self.doc_id_map[doc_id]
            if url in visited_urls:
                continue
            else:
                visited_urls.add(url)
            
            results.append({
                'url': url,
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

    def run_queries(self, queries: List[str]) -> None:
        with open("progress_report.txt", 'w') as f:
            for query in queries:
                print(f"\nRunning query: {query}")

                start_time = time.time()
                results = self.search(query)  
                elapsed_time = (time.time() - start_time) * 1000 

                top_results = results[:5]
                f.write(f"Found {len(results)} results for \"{query}\" in {elapsed_time:.2f} milliseconds:\n")
                for i, result in enumerate(top_results, 1):
                    f.write(f"{i}. {result['url']} (Score: {result['score']:.2f})\n")
                f.write("\n")

                #print it also 
                print(f"Found {len(results)} results (showing top 5):")
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
    
    queries = [
    "cristina lopes",
    "machine learning",
    "ACM",
    "master of software engineering",
    "ICS department",
    "campus map",
    "donald bren",
    "UCI",
    "staff directory",
    "uci events now",
    "Dining hall",
    "research opportunities for undergraduates",

    "artificial intelligence",
    "machine learning algorithms",
    "deep learning tutorials",
    "cybersecurity threats",
    "network security",
    "cryptography basics",
    "algorithms and data structures",
    "sorting algorithms",
    "graph algorithms",
    "complexity analysis",
    "probability and statistics for CS",
    "statistical learning",
    "natural language processing",
    "computer vision",
    "reinforcement learning",
    "AI ethics",
    "malware detection",
    "penetration testing",
    "encryption techniques",
    "data mining",
    "big data analytics",
    "neural networks",
    "pattern recognition",
    "statistical inference",
    "machine learning model evaluation"
    ]
    search_engine.run_queries(queries)
    # search_engine.run() 