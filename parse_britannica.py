#!/usr/bin/env python3
"""
Parse Encyclopaedia Britannica ALTO XML files and extract entry titles, text, and images.
"""

import xml.etree.ElementTree as ET
import os
import re
from pathlib import Path


class BritannicaParser:
    """Parser for Encyclopaedia Britannica ALTO XML files."""

    # ALTO XML namespace
    ALTO_NS = {'alto': 'http://www.loc.gov/standards/alto/v3/alto.xsd'}

    def __init__(self, xml_path):
        """Initialize parser with path to ALTO XML file."""
        self.xml_path = xml_path
        self.tree = ET.parse(xml_path)
        self.root = self.tree.getroot()

    def get_image_path(self):
        """Extract the image file path from the XML."""
        file_name_elem = self.root.find('.//alto:fileName', self.ALTO_NS)
        if file_name_elem is not None:
            return file_name_elem.text
        return None

    def get_text_lines(self):
        """Extract all text lines from the page."""
        lines = []
        text_lines = self.root.findall('.//alto:TextLine', self.ALTO_NS)

        for text_line in text_lines:
            # Get all String elements in this line
            strings = text_line.findall('.//alto:String', self.ALTO_NS)
            words = []

            for string in strings:
                content = string.get('CONTENT', '')
                if content:
                    words.append(content)

            if words:
                lines.append(' '.join(words))

        return lines

    def extract_entries(self):
        """
        Extract encyclopedia entries from the text.
        An entry typically starts with an all-caps word or phrase followed by a comma.
        """
        lines = self.get_text_lines()
        entries = []
        current_entry = None

        for line in lines:
            # Check if this line starts a new entry (all caps word followed by comma or period)
            # Pattern: starts with uppercase word(s), may have comma
            match = re.match(r'^([A-Z][A-Z\s\-]+?)(?:,|\.|$)', line)

            if match and len(match.group(1)) > 2:  # At least 3 chars to avoid false positives
                # Start a new entry
                if current_entry:
                    entries.append(current_entry)

                title = match.group(1).strip()
                current_entry = {
                    'title': title,
                    'text': line
                }
            elif current_entry:
                # Continue the current entry
                current_entry['text'] += ' ' + line

        # Add the last entry
        if current_entry:
            entries.append(current_entry)

        return entries

    def find_local_image(self):
        """Find the corresponding image file in the local directory structure."""
        xml_path = Path(self.xml_path)
        # Get the base name without extension (e.g., 188084090.34)
        base_name = xml_path.stem
        # Extract the numeric part before the last dot (e.g., 188084090)
        image_base = base_name.split('.')[0]

        # Look for image in sibling 'image' directory
        xml_dir = xml_path.parent
        image_dir = xml_dir.parent / 'image'

        if image_dir.exists():
            # Try common image extensions
            for ext in ['.jpg', '.jpeg', '.png', '.jp2']:
                # Try with the base number and various suffixes
                for suffix in ['.3', '.34', '']:
                    image_file = image_dir / f"{image_base}{suffix}{ext}"
                    if image_file.exists():
                        return str(image_file)

        return None

    def parse(self):
        """Parse the XML file and return structured data."""
        image_path_xml = self.get_image_path()  # Path from XML metadata
        image_path_local = self.find_local_image()  # Actual local image file
        entries = self.extract_entries()

        # If no entries were found, treat all text as a single entry
        if not entries:
            lines = self.get_text_lines()
            if lines:
                entries = [{
                    'title': 'Unknown',
                    'text': ' '.join(lines)
                }]

        return {
            'xml_file': self.xml_path,
            'image_path_xml': image_path_xml,  # Original path from XML
            'image_path': image_path_local,     # Local image file
            'entries': entries
        }


def parse_britannica_file(xml_path):
    """
    Parse a single Britannica ALTO XML file.

    Args:
        xml_path: Path to the ALTO XML file

    Returns:
        Dictionary with entries, image path, and metadata
    """
    parser = BritannicaParser(xml_path)
    return parser.parse()


def parse_britannica_directory(directory_path, recursive=True):
    """
    Parse all ALTO XML files in a directory.

    Supports multiple ID subdirectories with structure: /{ID_NUMBER}/alto/*.xml
    Each ID directory should have corresponding images in /{ID_NUMBER}/image/

    Args:
        directory_path: Path to directory containing ALTO XML files or ID subdirectories
        recursive: If True, recursively search all subdirectories (default: True)

    Yields:
        Dictionary with parsed data for each file
    """
    directory = Path(directory_path)

    # Recursively find all XML files in subdirectories
    pattern = '**/*.xml' if recursive else '*.xml'
    xml_files = directory.glob(pattern)

    for xml_file in xml_files:
        try:
            yield parse_britannica_file(str(xml_file))
        except Exception as e:
            print(f"Error parsing {xml_file}: {e}")


def scan_britannica_collection(base_path):
    """
    Scan a Britannica collection directory and identify all ID subdirectories.

    Args:
        base_path: Path to the base directory containing ID subdirectories

    Returns:
        List of dictionaries with information about each ID directory
    """
    base = Path(base_path)
    id_dirs = []

    # Find all subdirectories that look like ID directories (numeric names)
    for item in base.iterdir():
        if item.is_dir() and item.name.isdigit():
            alto_dir = item / 'alto'
            image_dir = item / 'image'

            # Count files in each directory
            xml_count = len(list(alto_dir.glob('*.xml'))) if alto_dir.exists() else 0
            image_count = len(list(image_dir.glob('*.*'))) if image_dir.exists() else 0

            id_dirs.append({
                'id': item.name,
                'path': str(item),
                'alto_dir': str(alto_dir) if alto_dir.exists() else None,
                'image_dir': str(image_dir) if image_dir.exists() else None,
                'xml_count': xml_count,
                'image_count': image_count
            })

    return sorted(id_dirs, key=lambda x: x['id'])


def parse_britannica_collection(base_path, verbose=False):
    """
    Parse an entire Britannica collection with multiple ID subdirectories.

    Args:
        base_path: Path to the base directory containing ID subdirectories
        verbose: If True, print progress information

    Yields:
        Dictionary with parsed data for each file, including ID directory info
    """
    base = Path(base_path)

    # Scan for ID directories
    id_dirs = scan_britannica_collection(base_path)

    if verbose:
        print(f"Found {len(id_dirs)} ID directories")
        total_xml = sum(d['xml_count'] for d in id_dirs)
        print(f"Total XML files: {total_xml}")

    # Parse each ID directory
    for id_dir in id_dirs:
        if verbose:
            print(f"Parsing ID {id_dir['id']}: {id_dir['xml_count']} files...")

        if id_dir['alto_dir']:
            for result in parse_britannica_directory(id_dir['alto_dir'], recursive=False):
                # Add ID to the result
                result['collection_id'] = id_dir['id']
                yield result


def main():
    """Example usage: parse and print entries from sample data."""
    import sys
    import argparse
    import json

    parser = argparse.ArgumentParser(description='Parse Encyclopaedia Britannica ALTO XML files')
    parser.add_argument('path', help='Path to XML file or directory')
    parser.add_argument('--json', '-j', dest='json_output', metavar='FILE',
                        help='Write output to JSON file instead of printing')
    parser.add_argument('--text-only', action='store_true',
                        help='Only include title and text in output (exclude image paths)')

    args = parser.parse_args()
    path = args.path

    results = []

    if os.path.isfile(path):
        # Parse single file
        result = parse_britannica_file(path)
        results.append(result)

        if not args.json_output:
            print(f"\n{'='*80}")
            print(f"XML File: {result['xml_file']}")
            print(f"Image File: {result['image_path']}")
            print(f"{'='*80}\n")

            for entry in result['entries']:
                print(f"Title: {entry['title']}")
                print(f"Text: {entry['text'][:200]}..." if len(entry['text']) > 200 else f"Text: {entry['text']}")
                print(f"Image: {result['image_path']}")
                print(f"{'-'*80}\n")

    elif os.path.isdir(path):
        # Parse directory
        for result in parse_britannica_directory(path):
            results.append(result)

            if not args.json_output:
                print(f"\n{'='*80}")
                print(f"XML File: {result['xml_file']}")
                print(f"Image File: {result['image_path']}")
                print(f"Number of entries: {len(result['entries'])}")
                print(f"{'='*80}\n")

                for entry in result['entries']:
                    print(f"Title: {entry['title']}")
                    print(f"Text: {entry['text'][:200]}..." if len(entry['text']) > 200 else f"Text: {entry['text']}")
                    print(f"Image: {result['image_path']}")
                    print(f"{'-'*80}\n")
    else:
        print(f"Error: {path} is not a valid file or directory")
        sys.exit(1)

    # Write to JSON file if specified
    if args.json_output:
        # Filter results if text-only mode is enabled
        if args.text_only:
            filtered_results = []
            for result in results:
                filtered_result = {
                    'entries': [{'title': entry['title'], 'text': entry['text']}
                               for entry in result['entries']]
                }
                # Include collection_id if present
                if 'collection_id' in result:
                    filtered_result['collection_id'] = result['collection_id']
                filtered_results.append(filtered_result)
            output_data = filtered_results
        else:
            output_data = results

        with open(args.json_output, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        print(f"Wrote {len(output_data)} result(s) to {args.json_output}")


if __name__ == '__main__':
    main()
