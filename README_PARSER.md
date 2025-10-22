# Encyclopaedia Britannica XML Parser

Python parser for Encyclopaedia Britannica ALTO XML files that extracts entry titles, text content, and image paths.

## Features

- Parse single XML files or entire directory structures
- Support for multiple ID subdirectories (e.g., `/144133901/alto/`, `/144133902/alto/`)
- Automatically finds corresponding image files
- Extracts entry titles and text content
- Export to JSON format for bot development
- Collection statistics and search functionality

## Directory Structure

The parser expects data organized as:

```
base_directory/
├── 144133901/
│   ├── alto/
│   │   ├── 188084090.34.xml
│   │   ├── 188084610.34.xml
│   │   └── ...
│   └── image/
│       ├── 188084090.3.jpg
│       ├── 188084610.3.jpg
│       └── ...
├── 144133902/
│   ├── alto/
│   └── image/
└── ...
```

Each numeric ID directory contains:
- `alto/` - ALTO XML files with OCR'd text
- `image/` - Corresponding page images

## Installation

No external dependencies required - uses only Python standard library:
- `xml.etree.ElementTree`
- `pathlib`
- `re`
- `json`

## Quick Start

### Parse a Single File

```python
from parse_britannica import parse_britannica_file

result = parse_britannica_file("path/to/file.xml")

for entry in result['entries']:
    print(f"Title: {entry['title']}")
    print(f"Text: {entry['text']}")
    print(f"Image: {result['image_path']}")
```

### Parse a Single ID Directory

```python
from parse_britannica import parse_britannica_directory

for result in parse_britannica_directory("144133901/alto"):
    for entry in result['entries']:
        print(f"{entry['title']}: {entry['text'][:100]}")
```

### Parse Multiple ID Directories

```python
from parse_britannica import parse_britannica_collection

# Automatically finds all ID subdirectories
for result in parse_britannica_collection("base_directory", verbose=True):
    collection_id = result['collection_id']
    for entry in result['entries']:
        print(f"[{collection_id}] {entry['title']}")
```

### Scan Collection Structure

```python
from parse_britannica import scan_britannica_collection

id_dirs = scan_britannica_collection("base_directory")

for id_dir in id_dirs:
    print(f"ID: {id_dir['id']}")
    print(f"  XML files: {id_dir['xml_count']}")
    print(f"  Image files: {id_dir['image_count']}")
```

## Command Line Usage

```bash
# Parse a single file
python parse_britannica.py path/to/file.xml

# Parse a directory (recursive)
python parse_britannica.py path/to/directory

# Run collection examples
python example_collection.py

# Run basic examples
python example_usage.py
```

## API Reference

### `parse_britannica_file(xml_path)`
Parse a single ALTO XML file.

**Returns:**
```python
{
    'xml_file': str,              # Path to XML file
    'image_path': str,            # Local image file path
    'image_path_xml': str,        # Original path from XML
    'entries': [
        {
            'title': str,         # Entry title
            'text': str           # Entry text content
        }
    ]
}
```

### `parse_britannica_directory(directory_path, recursive=True)`
Parse all XML files in a directory.

**Args:**
- `directory_path` - Directory containing XML files
- `recursive` - Search subdirectories (default: True)

**Yields:** Results from `parse_britannica_file()`

### `parse_britannica_collection(base_path, verbose=False)`
Parse entire collection with multiple ID subdirectories.

**Args:**
- `base_path` - Base directory containing ID subdirectories
- `verbose` - Print progress information

**Yields:** Results with added `collection_id` field

### `scan_britannica_collection(base_path)`
Scan and identify all ID subdirectories.

**Returns:** List of dictionaries:
```python
[
    {
        'id': str,                # ID directory name
        'path': str,              # Full path to ID directory
        'alto_dir': str,          # Path to alto/ subdirectory
        'image_dir': str,         # Path to image/ subdirectory
        'xml_count': int,         # Number of XML files
        'image_count': int        # Number of image files
    }
]
```

## Examples

The `example_collection.py` script demonstrates:

1. **Scanning** - Discover all ID directories and count files
2. **Parsing** - Process entire collections with progress tracking
3. **Recursive Search** - Simple recursive directory parsing
4. **JSON Export** - Save structured data for bot use
5. **Searching** - Find entries across all collections
6. **Statistics** - Gather collection statistics

## Export Formats

### Bot-Ready JSON

```python
{
    "id": "0_albion",
    "title": "ALBION",
    "content": "ALBION, the ancient name of Britain...",
    "image_path": "path/to/image.jpg",
    "metadata": {
        "source_xml": "path/to/source.xml",
        "character_count": 126,
        "word_count": 21
    }
}
```

### Collection JSON

```python
{
    "total_collections": 1,
    "total_files": 832,
    "total_entries": 5868,
    "collections": [
        {
            "id": "144133901",
            "files": [...],
            "entries": [...]
        }
    ]
}
```

## Use Cases

1. **Encyclopedia Bot** - Post random entries from the collection
2. **Search Engine** - Index and search historical encyclopedia content
3. **Text Analysis** - Study historical language and knowledge
4. **Digital Archive** - Create structured database from ALTO XML
5. **Content Mining** - Extract specific topics or patterns

## Statistics from Sample

The sample directory contains:
- 832 XML files
- 832 image files
- 5,868 encyclopedia entries
- ~680,000 total words
- Average 116 words per entry

## Notes

- The parser handles OCR errors gracefully (old spelling, artifacts)
- Entry detection is based on ALL-CAPS titles followed by comma or period
- Images are automatically matched by filename patterns
- Supports `.jpg`, `.jpeg`, `.png`, and `.jp2` image formats
- Works with Python 3.6+

## License

This parser is for working with public domain Encyclopaedia Britannica data from the National Library of Scotland.
