#!/bin/bash
set -e

# Function to log with timestamp
log_with_timestamp() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a logs.txt
}

# Initialize log file
log_with_timestamp "Starting RERA data processing pipeline"

log_with_timestamp "Scraping actionids"
python actionid-1.py

log_with_timestamp "Converting actionids to csv"
python json-to-csv-2.py

log_with_timestamp "Deleting actionid.json"
rm -f './utils/actionid.json'

log_with_timestamp "Running residential shell scripts..."
bash "./residential/run-residential-scripts.sh"

log_with_timestamp "Running plotted shell scripts..."
bash './plotted/run-plotted-scripts.sh'

log_with_timestamp "Shell scripts completed."

log_with_timestamp "Running plotted upload script"
node update-plotted.js

log_with_timestamp "Running residential upload script"
node update-residential.js

log_with_timestamp "Deleting final merged files after upload"
rm -f './residential/final-rera-residential.json'
rm -f './plotted/final-rera-plotted.json'

log_with_timestamp "All tasks completed successfully!"