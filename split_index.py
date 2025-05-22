import json
import os
from typing import Dict, List

def create_index_directory(base_dir: str) -> str:
    """Create the index directory if it doesn't exist."""
    index_dir = os.path.join(base_dir, "DEV_index")
    if not os.path.exists(index_dir):
        os.makedirs(index_dir)
    return index_dir

def get_term_range(token: str) -> str:
    """Get the identifier for a token (e.g., 'a' for tokens starting with a)."""
    return token[0].lower()

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
            data = json.loads(line)
            token = data['token']
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
    create_index_directory('.')
    # Split the index file
    split_index(
        input_file="DEV_final.jsonl",
        base_dir="."
    ) 