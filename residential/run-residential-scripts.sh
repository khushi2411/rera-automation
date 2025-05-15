# Exit on error
set -e

cd residential

# Run scrapy crawlers

echo "scraping residential basicdetails.."
scrapy crawl basicdetails
echo "scraping residential floorplan.."
scrapy crawl floorplan
echo "scraping residential inventory.."
scrapy crawl inventory
echo "scraping residential projectschedule.."
scrapy crawl projectschedule
echo "scraping residential towers.."
scrapy crawl towers
echo "scraping residential units.."
scrapy crawl units

echo "Scrapy crawls completed."

echo "combining all residential fragmented data into a json"
python all-residential.py


echo "deleting fragmented data"
rm -f floorplan.json
rm -f inventory.json
rm -f projectdetails.json
rm -f projectschedule.json
rm -f tower_data.json
rm -f unit_details.json
rm -f residential.csv


echo "Residential processing complete! Exit :)"
cd ..