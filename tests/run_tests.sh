#!/bin/bash

# Test script for best_name CLI tool
# Tests each file in tests/ directory with default configuration only

# Output file
OUTPUT_FILE="test_results.csv"

# Initialize CSV file with headers
echo "timestamp,original_filename,suggested_name" > "$OUTPUT_FILE"

echo "Starting best_name testing..."
echo "Results will be saved to: $OUTPUT_FILE"
echo "Testing $(ls tests/test_files/ | wc -l) files with default configuration"
echo

# Loop through each file in tests/test_files directory
for test_file in tests/test_files/*; do
    # Skip if not a file
    if [ ! -f "$test_file" ]; then
        continue
    fi
    
    original_filename=$(basename "$test_file")
    echo "Testing: $original_filename"
    
    # Get current timestamp
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    # Run best_name: capture stdout only, suppress stderr, save exit status
    suggested_name=$(best_name "$test_file" 2>/dev/null)
    exit_status=$?
    
    # Handle errors or empty responses
    if [ $exit_status -ne 0 ] || [ -z "$suggested_name" ]; then
        suggested_name="ERROR: Failed to generate suggestion"
        echo "  ⚠️  Error (exit code: $exit_status)"
    else
        echo "  ✓ Success: $suggested_name"
    fi
    
    # Escape any commas in the suggested name for CSV format
    suggested_name=$(echo "$suggested_name" | sed 's/,/;/g')
    
    # Write to CSV file
    echo "$timestamp,$original_filename,$suggested_name" >> "$OUTPUT_FILE"
    
    # Brief pause between API calls to avoid rate limiting
    sleep 1
done

echo
echo "Testing completed! Results saved to: $OUTPUT_FILE"
echo
echo "Summary:"
echo "- Files tested: $(ls tests/test_files/ | wc -l)"
echo "- Errors: $(grep -c "ERROR:" "$OUTPUT_FILE")"
echo
echo "You can view the results with:"
echo "cat $OUTPUT_FILE"