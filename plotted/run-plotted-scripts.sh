# Exit on error
set -e

# Function to log with timestamp
log_with_timestamp() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a ../logs.txt
}

cd plotted

log_with_timestamp "Starting plotted data processing"

# Run scrapy crawlers
log_with_timestamp "Scraping plotted developmentdetails..."
scrapy crawl developmentdetails
log_with_timestamp "Scraping plotted projectdetails..."
scrapy crawl projectdetails

log_with_timestamp "All plotted scrapy crawls completed successfully"

log_with_timestamp "Combining plotted fragmented data"
python combine-plotted.py

log_with_timestamp "Deleting plotted fragmented data files"
rm -f developmentdetails.json
rm -f plotted.csv
rm -f projectdetails.json

log_with_timestamp "Plotted data processing complete!"
cd ..