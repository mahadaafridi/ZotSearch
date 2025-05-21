import json
import os
from typing import Dict, List

def create_index_directory(base_dir: str) -> str:
    """Create the index directory if it doesn't exist."""
    index_dir = os.path.join(base_dir, "ANALYST_index")
    if not os.path.exists(index_dir):
        os.makedirs(index_dir)
    return index_dir

def get_term_range(token: str) -> str:
    """Get the letter identifier for a token (e.g., 'a' for tokens starting with a)."""
    first_char = token[0].lower()
    
    # Return the first character if it's a letter, otherwise return 'other'
    return first_char if first_char.isalpha() else 'other'

def split_index(input_file: str, base_dir: str) -> None:
    """
    Split the index file into separate files based on term ranges.
    
    Args:
        input_file (str): Path to the input index file
        base_dir (str): Base directory for output files
    """
    # Create index directory
    index_dir = create_index_directory(base_dir)
    
    # Dictionary to store terms and their postings for each range
    range_files = {}
    
    # Read and split the index
    with open(input_file, 'r') as f:
        for line in f:
            data = json.loads(line)
            token = data['token']
            range_id = get_term_range(token)
            
            # Initialize range file if not exists
            if range_id not in range_files:
                range_files[range_id] = []
            
            # Add to appropriate range
            range_files[range_id].append(data)
    
    # Write each range to a separate file
    for range_id, terms in range_files.items():
        output_file = os.path.join(index_dir, f"{range_id}.jsonl")
        
        # Sort terms within each range
        terms.sort(key=lambda x: x['token'])
        
        with open(output_file, 'w') as f:
            for term in terms:
                f.write(json.dumps(term) + '\n')
        
        print(f"Created index file for range {range_id}")

if __name__ == '__main__':
    # Split the index file
    split_index(
        input_file="ANALYST_final.jsonl",
        base_dir="."
    ) 