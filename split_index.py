import json
import os
from typing import Dict, List
from math import log

TOTAL_DOCUMENTS = 0

def initialize_total_documents(input_file: str) -> None:
    """
    Given an input file containing the corpus of documents, sets the TOTAL_DOCUMENTS global variable to reflect
    total number of documents in corpus
    """
    global TOTAL_DOCUMENTS
    with open(input_file, 'r') as f:
        count = 0
        for line in f:
            count += 1
    
    TOTAL_DOCUMENTS = count

def create_index_directory(base_dir: str) -> str:
    """Create the index directory if it doesn't exist."""
    index_dir = os.path.join(base_dir, "DEV_index")
    if not os.path.exists(index_dir):
        os.makedirs(index_dir)
    return index_dir

def get_term_range(token: str) -> str:
    """Get the identifier for a token (e.g., 'a' for tokens starting with a)."""
    return token[0].lower()

def calculate_tfidf(tf: int, df: int, fields: List[str]) -> float:
    """
    Calculates the tfidf with field boosting for the given tf and df.

    Args:
        tf (int): Raw Term Frequency of token
        df (int): Number of documents token is found in
    
    Returns:
        float: tf-idf score
    """
    tf = 1+log(tf)
    idf = log(TOTAL_DOCUMENTS/(1+df))
    field_boost = 1

    if 'title' in fields:
        field_boost *= 2
    if 'header' in fields:
        field_boost *= 1.5
    if 'strong' in fields:
        field_boost *= 1.3

    return tf * idf * field_boost

def split_index(input_file: str, base_dir: str) -> None:
    """
    Split the index file into separate files based on term ranges.
    
    Args:
        input_file (str): Path to the input index file
        base_dir (str): Base directory for output files
    """
    # Create index directory
    index_dir = create_index_directory(base_dir)
    
    # Store current id and postings associated with it
    current_id = None
    current_postings = []
    
    # Read and split the index into starting characters a-z, 0-9
    with open(input_file, 'r') as f:
        for line in f:
            data = json.loads(line) # Get line from jsonl
            token = data['token']
            df = len(data['postings']) # Get number of documents token is found in

            # Calculate tfidf for each posting
            for posting in data['postings']:
                posting['tfidf'] = calculate_tfidf(posting['tf'], df, posting['fields'])

            range_id = get_term_range(token)
            
            # Starting character has changed, dump current tokens and postings into separate file
            if range_id != current_id:
                if current_id is not None:
                    output_file = os.path.join(index_dir, f"{current_id}.jsonl")
                    
                    with open(output_file, 'w') as separate_index:
                        for term in current_postings:
                            json_line = json.dumps(term)
                            separate_index.write(json_line + '\n')
                        
                        print(f"Created index file for range {current_id}")
                
                current_id = range_id
                current_postings = []

            current_postings.append(data)
    
    # Once finished reading file, if we still have leftover info, dump to file
    if current_postings is not None:
        output_file = os.path.join(index_dir, f"{current_id}.jsonl")
        
        with open(output_file, 'w') as separate_index:
            for term in current_postings:
                json_line = json.dumps(term)
                separate_index.write(json_line + '\n')
            
            print(f"Created index file for range {current_id}")

if __name__ == '__main__':
    initialize_total_documents('DEV_doc_id.jsonl')
    create_index_directory('.')
    # Split the index file
    split_index(
        input_file="DEV_final.jsonl",
        base_dir="."
    ) 