#!/usr/bin/env python3
"""
Parse plain text Encyclopaedia Britannica files and extract entry titles and text.
"""

import os
import re
from pathlib import Path


class BritannicaTextParser:
    """Parser for plain text Encyclopaedia Britannica files."""

    def __init__(self, text_path):
        """Initialize parser with path to text file."""
        self.text_path = text_path

    def get_text_lines(self):
        """Read all lines from the text file."""
        with open(self.text_path, 'r', encoding='utf-8', errors='ignore') as f:
            return [line.rstrip() for line in f.readlines()]

    def is_valid_entry(self, text):
        """
        Check if an entry contains at least one complete sentence.
        Valid entries should have proper sentence structure with ending punctuation.
        """
        if not text or len(text.strip()) < 20:
            return False

        # Check for sentence-ending punctuation followed by space or end of string
        # This indicates at least one complete sentence
        if re.search(r'[.!?](\s|$)', text):
            # Also check that it has some actual words (not just punctuation and symbols)
            words = re.findall(r'\b[a-zA-Z]{3,}\b', text)
            return len(words) >= 5  # At least 5 words of 3+ letters

        return False

    def extract_entries(self):
        """
        Extract encyclopedia entries from the text.
        An entry typically starts with an all-caps word or phrase, often with punctuation.
        Skips the header/title page information and entries without complete sentences.
        """
        lines = self.get_text_lines()
        entries = []
        current_entry = None
        in_content = False

        # Common header words to skip
        skip_patterns = [
            'ENCYCLOPAEDIA BRITANNICA',
            'SEVENTH EDITION',
            'DICTIONARY',
            'VOLUME',
            'SCIENCES',
            'LITERATURE',
            'DISSERTATIONS',
            'SUPPLEMENT',
            'GENERAL INDEX',
            'ENGRAVINGS',
            'EDINBURGH'
        ]

        for line in lines:
            # Skip empty lines
            if not line.strip():
                continue

            line_stripped = line.strip()

            # Skip known header patterns
            if any(pattern in line_stripped for pattern in skip_patterns):
                continue

            # Check if this line starts a new entry
            # Pattern: line with mostly uppercase letters, may have comma or period
            # Should have at least one comma or period at the end
            match = re.match(r'^([A-Z][A-Z\s\-,]+?)[\.,]\s*$', line_stripped)

            if match:
                title = match.group(1).strip()
                # Additional validation: title should be at least 3 chars and not be a single letter
                if len(title) >= 3 and not re.match(r'^[A-Z]$', title):
                    # Mark that we're in content now
                    in_content = True

                    # Save the previous entry if it's valid
                    if current_entry and current_entry['text']:
                        if self.is_valid_entry(current_entry['text']):
                            entries.append(current_entry)

                    # Start a new entry
                    current_entry = {
                        'title': title,
                        'text': ''
                    }
                    continue

            # Only process content if we've found at least one entry
            if in_content and current_entry:
                # Continue the current entry
                # Skip very short lines that might be artifacts
                if len(line_stripped) > 2:
                    if current_entry['text']:
                        current_entry['text'] += ' ' + line_stripped
                    else:
                        current_entry['text'] = line_stripped

        # Add the last entry if it's valid
        if current_entry and current_entry['text']:
            if self.is_valid_entry(current_entry['text']):
                entries.append(current_entry)

        return entries

    def parse(self):
        """Parse the text file and return structured data."""
        entries = self.extract_entries()

        # If no entries were found, treat all text as a single entry
        if not entries:
            lines = self.get_text_lines()
            # Skip header lines and get actual content
            content_lines = [line for line in lines if line.strip() and len(line.strip()) > 2]
            if content_lines:
                entries = [{
                    'title': 'Unknown',
                    'text': ' '.join(content_lines)
                }]

        return {
            'text_file': self.text_path,
            'entries': entries
        }


def parse_britannica_text_file(text_path):
    """
    Parse a single Britannica plain text file.

    Args:
        text_path: Path to the text file

    Returns:
        Dictionary with entries and metadata
    """
    parser = BritannicaTextParser(text_path)
    return parser.parse()


def parse_britannica_text_directory(directory_path, recursive=True):
    """
    Parse all text files in a directory.

    Args:
        directory_path: Path to directory containing text files
        recursive: If True, recursively search all subdirectories (default: True)

    Yields:
        Dictionary with parsed data for each file
    """
    directory = Path(directory_path)

    # Recursively find all text files in subdirectories
    pattern = '**/*.txt' if recursive else '*.txt'
    text_files = directory.glob(pattern)

    for text_file in text_files:
        try:
            yield parse_britannica_text_file(str(text_file))
        except Exception as e:
            print(f"Error parsing {text_file}: {e}")


def main():
    """Example usage: parse and print entries from text files."""
    import sys
    import argparse
    import json

    parser = argparse.ArgumentParser(description='Parse plain text Encyclopaedia Britannica files')
    parser.add_argument('path', help='Path to text file or directory')
    parser.add_argument('--json', '-j', dest='json_output', metavar='FILE',
                        help='Write output to JSON file instead of printing')
    parser.add_argument('--text-only', action='store_true',
                        help='Only include title and text in output (exclude file paths)')

    args = parser.parse_args()
    path = args.path

    results = []

    if os.path.isfile(path):
        # Parse single file
        result = parse_britannica_text_file(path)
        results.append(result)

        if not args.json_output:
            print(f"\n{'='*80}")
            print(f"Text File: {result['text_file']}")
            print(f"Number of entries: {len(result['entries'])}")
            print(f"{'='*80}\n")

            for entry in result['entries']:
                print(f"Title: {entry['title']}")
                print(f"Text: {entry['text'][:200]}..." if len(entry['text']) > 200 else f"Text: {entry['text']}")
                print(f"{'-'*80}\n")

    elif os.path.isdir(path):
        # Parse directory
        for result in parse_britannica_text_directory(path):
            results.append(result)

            if not args.json_output:
                print(f"\n{'='*80}")
                print(f"Text File: {result['text_file']}")
                print(f"Number of entries: {len(result['entries'])}")
                print(f"{'='*80}\n")

                for entry in result['entries']:
                    print(f"Title: {entry['title']}")
                    print(f"Text: {entry['text'][:200]}..." if len(entry['text']) > 200 else f"Text: {entry['text']}")
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
                filtered_results.append(filtered_result)
            output_data = filtered_results
        else:
            output_data = results

        with open(args.json_output, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        print(f"Wrote {len(output_data)} result(s) to {args.json_output}")


if __name__ == '__main__':
    main()
