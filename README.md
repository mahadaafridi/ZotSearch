# ZotSearch

A full-featured search engine implementation built specifically for UCI (University of California, Irvine) domain content. Built with Python Flask backend and modern React frontend, ZotSearch crawls and indexes UCI web pages to provide fast, relevant search results for the UCI community. The project implements a custom inverted index for efficient document retrieval across UCI's web presence.

## Features

- **UCI Domain Focus**: Specialized search engine for UCI web content and academic resources
- **Inverted Index**: Efficient indexing of UCI documents with TF-IDF scoring
- **Web Interface**: Modern, responsive search interface built with React and Tailwind CSS
- **Document Retrieval**: Fast search across indexed UCI corpus (55,000+ pages)
- **Stemming**: Porter stemmer for improved search accuracy
- **Academic Content Optimization**: Enhanced ranking for important academic elements (titles, headings, bold text)
- **Near-Duplicate Detection**: Identifies and handles near-duplicate UCI pages
- **Split Index Architecture**: Optimized for memory efficiency with split index files

## Tech Stack

- **Backend**: Python Flask with CORS support
- **Frontend**: React with Tailwind CSS
- **Text Processing**: NLTK Porter Stemmer, BeautifulSoup for HTML parsing
- **Data Storage**: JSON Lines format for document storage
- **Memory Management**: Pympler for memory optimization

## Project Structure

```
├── app.py                 # Flask web application entry point
├── search.py              # Search engine implementation with TF-IDF scoring
├── inverted_index.py      # Inverted index creation and management
├── Posting.py             # Posting list data structure
├── split_index.py         # Index splitting for memory optimization
├── templates/
│   └── index.html         # React-based search interface
└── README.md             # This file
```

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd Assignment_3_M1
   ```

2. **Install Python dependencies**:
   ```bash
   pip install flask flask-cors nltk beautifulsoup4 pympler
   ```

3. **Download NLTK data** (if needed):
   ```python
   import nltk
   nltk.download('punkt')
   ```

## Usage

### Building the Index

Before running the search engine, you need to build the inverted index from your document corpus:

```python
from inverted_index import InvertedIndex

# Initialize and build index
indexer = InvertedIndex()
# Add your document processing logic here
```

### Running ZotSearch

1. **Start the Flask server**:
   ```bash
   python app.py
   ```

2. **Access the web interface**:
   Open your browser and navigate to `http://localhost:5000`

3. **Search UCI content**:
   - Enter your search query in the search box
   - Press Enter or click the search button
   - View ranked results with relevance scores

### API Endpoints

- `GET /` - Serves the main search interface
- `GET /search?query=<search_terms>` - Returns search results in JSON format

Example API usage:
```bash
curl "http://localhost:5000/search?query=information%20retrieval"
```

## Implementation Details

### Inverted Index
- Uses Porter stemming for term normalization
- Implements TF-IDF scoring for document ranking
- Supports field-based indexing (title, headers, body text)
- Memory-efficient partial index creation with configurable thresholds

### Search Algorithm
- Boolean AND queries with stemming
- TF-IDF cosine similarity scoring
- Concurrent processing for improved performance
- Stop word filtering for query optimization

### Index Splitting
- Alphabetical splitting of terms for memory optimization
- Separate index files for different character ranges
- Document ID mapping for efficient retrieval

## Configuration

Key configuration options in the code:

- **Index Directory**: `DEV_index/` (configurable in `app.py`)
- **Document ID File**: `DEV_doc_id.jsonl`
- **Memory Threshold**: 20MB for partial index dumps
- **Server Port**: 5000 (configurable in `app.py`)

## Performance Features

- **Memory Management**: Configurable memory thresholds for index building
- **Concurrent Processing**: Multi-threaded search execution
- **Efficient Storage**: JSON Lines format for fast I/O
- **Optimized Retrieval**: Split index architecture for reduced memory footprint

## Development

### Adding New Features

1. **Backend changes**: Modify `search.py` or `inverted_index.py`
2. **Frontend changes**: Update the React components in `templates/index.html`
3. **API changes**: Modify routes in `app.py`

## Dependencies

- `flask` - Web framework
- `flask-cors` - Cross-origin resource sharing
- `nltk` - Natural language processing
- `beautifulsoup4` - HTML parsing
- `pympler` - Memory profiling

