#!/usr/bin/env python3
# /// script
# dependencies = [
#   "PyYAML"
# ]
# ///

import os
import re
import yaml


def convert_file(logseq_filepath: str) -> None:
    """
    Convert a Logseq-formatted Markdown file to Obsidian format with YAML frontmatter.
    
    Args:
        logseq_filepath: Path to the Logseq-formatted Markdown file
    """
    # Determine the output filepath
    base_name = os.path.basename(logseq_filepath)
    dir_name = os.path.dirname(logseq_filepath)
    
    # Remove .md extension, add _ob suffix, then add .md back
    if base_name.lower().endswith('.md'):
        output_filename = f"{base_name[:-3]}_ob.md"
    else:
        output_filename = f"{base_name}_ob.md"
    
    output_filepath = os.path.join(dir_name, output_filename)
    
    # Read the input file
    with open(logseq_filepath, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Extract properties and remaining content
    properties, remaining_content = extract_properties(content)
    
    # Convert properties to YAML frontmatter
    yaml_frontmatter = convert_to_yaml(properties)
    
    # Write the output file
    with open(output_filepath, 'w', encoding='utf-8') as file:
        file.write(f"---\n{yaml_frontmatter}---\n\n{remaining_content}")
    
    print(f"Conversion complete. Output file: {output_filepath}")


def extract_properties(content: str) -> tuple:
    """
    Extract Logseq properties from the content.
    
    Args:
        content: The content of the Logseq file
    
    Returns:
        tuple: (properties_dict, remaining_content)
    """
    lines = content.split('\n')
    properties = {}
    property_pattern = re.compile(r'^([^:]+)::\s*(.*)$')
    
    # Find the index where properties end
    end_index = 0
    for i, line in enumerate(lines):
        match = property_pattern.match(line.strip())
        if match and i == end_index:  # Must be contiguous from the start
            key, value = match.groups()
            properties[key.strip()] = value.strip()
            end_index = i + 1
        elif i > 0 and end_index > 0 and (line.strip() == '' or not match):
            # Stop at first non-property line or empty line after at least one property
            break
    
    # Get the remaining content
    remaining_content = '\n'.join(lines[end_index:])
    
    return properties, remaining_content


def convert_to_yaml(properties: dict) -> str:
    """
    Convert Logseq properties to YAML format.
    
    Args:
        properties: Dictionary of Logseq properties
    
    Returns:
        str: YAML formatted string
    """
    ALWAYS_LIST_KEYS = {'tags', 'aliases'}
    yaml_dict = {}

    for original_key, value_str in properties.items():
        normalized_key = original_key.lower()
        processed_value = None # Default

        if normalized_key in ALWAYS_LIST_KEYS:
            if not value_str:
                processed_value = []
            else:
                items = []
                for item_val in value_str.split(','):
                    stripped_item = item_val.strip()
                    items.append(None if stripped_item == '' else stripped_item)
                processed_value = items
        elif ',' in value_str:
            items = []
            for item_val in value_str.split(','):
                stripped_item = item_val.strip()
                items.append(None if stripped_item == '' else stripped_item)
            processed_value = items
        else:
            processed_value = None if value_str == '' else value_str
        
        yaml_dict[original_key] = processed_value
    
    # Define a custom representer for None values to output as empty
    def represent_none_as_empty(dumper, data):
        return dumper.represent_scalar('tag:yaml.org,2002:null', '')

    yaml.add_representer(type(None), represent_none_as_empty)

    # Convert to YAML string
    yaml_str = yaml.dump(yaml_dict, sort_keys=False, allow_unicode=True, default_flow_style=False)
    
    return yaml_str


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python logseq2obsidian.py <logseq_filepath>")
        sys.exit(1)
    
    logseq_filepath = sys.argv[1]
    convert_file(logseq_filepath)