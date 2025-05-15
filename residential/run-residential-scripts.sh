# Exit on error
set -e

# Function to log with timestamp
log_with_timestamp() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a ../logs.txt
}

cd residential

log_with_timestamp "Starting residential data processing"

# Run scrapy crawlers
log_with_timestamp "Scraping residential basicdetails..."
scrapy crawl basicdetails
log_with_timestamp "Scraping residential floorplan..."
scrapy crawl floorplan
log_with_timestamp "Scraping residential inventory..."
scrapy crawl inventory
log_with_timestamp "Scraping residential projectschedule..."
scrapy crawl projectschedule
log_with_timestamp "Scraping residential towers..."
scrapy crawl towers
log_with_timestamp "Scraping residential units..."
scrapy crawl units

log_with_timestamp "All scrapy crawls completed successfully"

log_with_timestamp "Combining all residential fragmented data into a JSON file"
python all-residential.py

log_with_timestamp "Deleting fragmented data files"
rm -f floorplan.json
rm -f inventory.json
rm -f projectdetails.json
rm -f projectschedule.json
rm -f tower_data.json
rm -f unit_details.json
rm -f residential.csv

log_with_timestamp "Residential processing complete! Exit :)"
cd ..