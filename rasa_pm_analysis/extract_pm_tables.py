import re
import os

def convert_to_markdown_table(title, header_line, separator_line, data_lines):
    # Try to get column start and end positions from the separator_line
    col_spans = []
    for match in re.finditer(r"(-+)", separator_line):
        col_spans.append(match.span())

    if not col_spans:
        # Fallback: if spans can't be determined, try splitting by multiple spaces
        # This is less reliable for plain text tables that might use single spaces within cells
        headers = [h.strip() for h in re.split(r" {2,}", header_line.strip())]
        if not headers or not headers[0]: # Skip if header parsing fails badly
            return None
        num_cols = len(headers)
        
        md_table_lines = [f"| {' | '.join(headers)} |"]
        md_table_lines.append(f"|{'|'.join(['---'] * num_cols)}|")
        for line in data_lines:
            row_data = [rd.strip() for rd in re.split(r" {2,}", line.strip())]
            # Ensure consistent number of columns
            if len(row_data) < num_cols:
                row_data.extend([''] * (num_cols - len(row_data)))
            md_table_lines.append(f"| {' | '.join(row_data[:num_cols])} |")
        return f"# {title}\n\n" + "\n".join(md_table_lines) + "\n"

    # Using column spans determined from the separator line
    def parse_line_with_spans(line, spans):
        cols = []
        # Pad line to ensure all spans can be accessed
        # Max end position needed from spans
        max_end = 0
        if spans:
            max_end = max(s[1] for s in spans)
        padded_line = line.rstrip().ljust(max_end)
        for start, end in spans:
            cols.append(padded_line[start:end].strip())
        return cols

    headers = parse_line_with_spans(header_line, col_spans)
    if not headers or not any(h for h in headers): # If headers are all empty, parsing failed
        print(f"Warning: Header parsing failed for title '{title}' with spans. Header: '{header_line}', Spans: {col_spans}")
        # Fallback to space splitting for this specific table if span parsing fails header
        headers_fallback = [h.strip() for h in re.split(r" {2,}", header_line.strip())]
        if not headers_fallback or not headers_fallback[0]: return None
        num_cols = len(headers_fallback)
        md_table_lines = [f"| {' | '.join(headers_fallback)} |"]
        md_table_lines.append(f"|{'|'.join(['---'] * num_cols)}|")
        for line_idx, data_line_content in enumerate(data_lines):
            row_data_fallback = [rd.strip() for rd in re.split(r" {2,}", data_line_content.strip())]
            if len(row_data_fallback) < num_cols: row_data_fallback.extend([''] * (num_cols - len(row_data_fallback)))
            md_table_lines.append(f"| {' | '.join(row_data_fallback[:num_cols])} |")
        return f"# {title}\n\n" + "\n".join(md_table_lines) + "\n"

    md_table_lines = [f"| {' | '.join(headers)} |"]
    md_table_lines.append(f"|{'|'.join(['---'] * len(headers))}|")

    for line_content in data_lines:
        row_data = parse_line_with_spans(line_content, col_spans)
        md_table_lines.append(f"| {' | '.join(row_data)} |")
        
    return f"# {title}\n\n" + "\n".join(md_table_lines) + "\n"

def extract_and_save_tables(markdown_file_path, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    with open(markdown_file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.split('\n')
    table_count = {}
    written_table_hashes = set()
    i = 0
    print(f"Starting table extraction from {markdown_file_path}. Total lines: {len(lines)}")

    while i < len(lines):
        line = lines[i]
        
        # Heuristic for separator line: starts with optional spaces, then multiple dash segments
        # Each segment must be at least two dashes. Segments separated by one or more spaces.
        # Example: "  ---  ----   ---"
        if re.match(r"^\s*(-{2,}(\s+-{2,})*)\s*$", line) and len(re.findall(r"(-+)", line)) > 1:
            separator_line_index = i
            separator_line = line
            print(f"Found potential separator line at index {separator_line_index}: '{separator_line}'")

            if separator_line_index == 0:
                i += 1
                continue
            header_line_index = separator_line_index - 1
            header_line = lines[header_line_index]
            
            if not header_line.strip() or re.match(r"^\s*(-{2,}(\s+-{2,})*)\s*$", header_line):
                print("Header line is empty or also a separator. Skipping.")
                i += 1
                continue
            print(f"Found potential header line: '{header_line}'")

            title_lines = []
            temp_idx = header_line_index - 1
            # Skip blank line if present
            if temp_idx >= 0 and not lines[temp_idx].strip():
                temp_idx -= 1
            
            # Collect title lines (non-blank, not starting with '######' unless it's the only line)
            while temp_idx >= 0 and lines[temp_idx].strip():
                current_title_line = lines[temp_idx].strip()
                if current_title_line.startswith("###### ") and title_lines: # Stop if it's a new section header and we already have title parts
                    break
                # Stop if we hit what looks like another table's data or separator from a table above
                if re.match(r"^\s*(-{2,}(\s+-{2,})*)\s*$", current_title_line):
                    break
                title_lines.insert(0, current_title_line)
                if len(title_lines) > 3: # Limit title to a few lines
                    break 
                temp_idx -= 1
            
            table_title = " ".join(title_lines) if title_lines else "Extracted_Table"
            if not table_title.strip() or "###### ChatGPT said:" in table_title : table_title = "Extracted_Table"
            # If title is just 'Now interactive!', try to get a better one
            if table_title.lower() == "now interactive!":
                # Look for specific known titles if the current one is too generic
                specific_title_search = re.search(r'(Loove Program Task Register|North 6th Building Task Queue|Studio Asset & Retail Strategy Tasks|Vertical Definitions Table|Initiative-Vertical Mapping)', "\n".join(lines[max(0,temp_idx-5):header_line_index]), re.IGNORECASE)
                if specific_title_search:
                    table_title = specific_title_search.group(0).strip()
                else:
                    table_title = "Extracted_Table"
            
            print(f"Determined title: '{table_title}'")

            data_lines = []
            data_idx = separator_line_index + 1
            while data_idx < len(lines) and lines[data_idx].strip():
                # Stop if we encounter another separator line or a clear section break
                if re.match(r"^\s*(-{2,}(\s+-{2,})*)\s*$", lines[data_idx]) or lines[data_idx].startswith("###### "):
                    break
                data_lines.append(lines[data_idx])
                data_idx += 1
            
            if not data_lines:
                print("No data lines found for this table. Skipping.")
                i = data_idx
                continue
            
            print(f"Found {len(data_lines)} data lines.")

            markdown_table_str = convert_to_markdown_table(table_title, header_line, separator_line, data_lines)

            if markdown_table_str:
                # Create a hash of the table content (excluding title) to avoid duplicates
                table_content_for_hash = "\n".join([header_line, separator_line] + data_lines)
                table_hash = hash(table_content_for_hash)

                if table_hash in written_table_hashes:
                    print(f"Skipping duplicate table content (hash match) for title '{table_title}'")
                    i = data_idx
                    continue
                written_table_hashes.add(table_hash)

                filename_base = re.sub(r'[^a-z0-9_]+', '_', table_title.lower()).strip('_')
                if not filename_base: filename_base = "table"

                current_count = table_count.get(filename_base, 0) + 1
                table_count[filename_base] = current_count
                filename = f"{filename_base}_{current_count}.md" if current_count > 1 else f"{filename_base}.md"
                
                output_path = os.path.join(output_dir, filename)
                with open(output_path, 'w', encoding='utf-8') as outfile:
                    outfile.write(markdown_table_str)
                print(f"Successfully extracted and wrote table '{table_title}' to {output_path}")
            else:
                print(f"Failed to convert table '{table_title}' to markdown format.")
            
            i = data_idx # Move past the processed table
        else:
            i += 1 # Move to the next line
    
    print("Table extraction process finished.")

if __name__ == '__main__':
    markdown_file = '/home/ubuntu/rasa_pm_thread.md'
    output_directory = '/home/ubuntu/pm_tables'
    extract_and_save_tables(markdown_file, output_directory)

