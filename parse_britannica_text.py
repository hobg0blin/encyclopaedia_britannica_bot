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

    def merge_duplicate_entries(self, entries):
        """
        Merge entries with the same or very similar titles.
        This handles cases where page headers create duplicate entries.
        """
        if not entries:
            return entries

        merged = {}
        for entry in entries:
            title = entry['title']

            # Normalize the title for comparison
            normalized_title = title.strip().rstrip(',.')

            if normalized_title in merged:
                # Merge with existing entry by appending text
                merged[normalized_title]['text'] += ' ' + entry['text']
            else:
                # New entry
                merged[normalized_title] = {
                    'title': normalized_title,
                    'text': entry['text']
                }

        return list(merged.values())

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

            # Check for single-line entries (title and text on same line)
            # Pattern: "TITLE, text here." or "TITLE. Text here."
            single_line_match = re.match(r'^([A-Z][A-Z\s\-]+?)([\.,])\s+(.+)$', line_stripped)

            if single_line_match:
                title = single_line_match.group(1).strip()
                text = single_line_match.group(3).strip()

                # Validate the title
                words = re.findall(r'\b[A-Z]{3,}\b', title)

                # Skip single-letter prefixes
                if re.match(r'^[A-Z]\s', title) or re.match(r'^[A-Z]$', title):
                    # Not a valid title, treat as continuation
                    if in_content and current_entry:
                        if current_entry['text']:
                            current_entry['text'] += ' ' + line_stripped
                        else:
                            current_entry['text'] = line_stripped
                    continue

                # Skip titles with excessive spacing
                if title.count(' ') > 10:
                    if in_content and current_entry:
                        if current_entry['text']:
                            current_entry['text'] += ' ' + line_stripped
                        else:
                            current_entry['text'] = line_stripped
                    continue

                # Must have enough content and valid title
                if len(title) >= 5 and len(words) >= 1 and len(text) > 10:
                    # Mark that we're in content now
                    in_content = True

                    # Save the previous entry if it's valid
                    if current_entry and current_entry['text']:
                        if self.is_valid_entry(current_entry['text']):
                            entries.append(current_entry)

                    # Create new complete entry
                    current_entry = {
                        'title': title,
                        'text': text
                    }

                    # This is a complete entry, save it
                    if self.is_valid_entry(current_entry['text']):
                        entries.append(current_entry)
                        current_entry = None
                    continue

            # Check for multi-line entries (title on its own line)
            # Pattern: line with mostly uppercase letters, may have comma or period at the end
            match = re.match(r'^([A-Z][A-Z\s\-,]+?)[\.,]\s*$', line_stripped)

            if match:
                title = match.group(1).strip().rstrip(',.')

                # Additional validation to avoid page headers and fragments:
                # 1. Title should be at least 5 characters
                # 2. Should not start with a single letter followed by space/comma (e.g., "M, ANIMAL", "H MAGNETISM")
                # 3. Should contain at least one complete word of 3+ letters
                # 4. Should not have excessive spacing (OCR artifact like "M A G N E T I S M")

                # Skip single-letter prefixes
                if re.match(r'^[A-Z]\s', title) or re.match(r'^[A-Z],', title):
                    continue

                # Skip titles with excessive spacing (more than 3 spaces suggests OCR issues)
                if title.count(' ') > 10:
                    continue

                words = re.findall(r'\b[A-Z]{3,}\b', title)

                if len(title) >= 5 and len(words) >= 1:
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

        # Merge duplicate entries
        entries = self.merge_duplicate_entries(entries)

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
    text_files = sorted(directory.glob(pattern))  # Sort files for consistent ordering

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
    parser.add_argument('--split', type=int, metavar='N',
                        help='Split output into multiple files with N entries each (only with --json)')

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

        # Split into multiple files if requested
        if args.split:
            # Flatten all entries from all results
            all_entries = []
            for result in output_data:
                all_entries.extend(result['entries'])

            # Get base filename without extension
            base_name = os.path.splitext(args.json_output)[0]
            ext = os.path.splitext(args.json_output)[1] or '.json'

            # Split into chunks
            total_files = 0
            for i in range(0, len(all_entries), args.split):
                chunk = all_entries[i:i + args.split]
                file_num = (i // args.split) + 1
                output_file = f"{base_name}_{file_num}{ext}"

                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump([{'entries': chunk}], f, indent=2, ensure_ascii=False)

                total_files += 1
                print(f"Wrote {len(chunk)} entries to {output_file}")

            print(f"Total: {len(all_entries)} entries across {total_files} file(s)")
        else:
            with open(args.json_output, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            print(f"Wrote {len(output_data)} result(s) to {args.json_output}")


if __name__ == '__main__':
    main()
