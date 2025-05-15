set -e


cd plotted

echo "scraping residential developmentdetails.."
scrapy crawl developmentdetails
echo "scraping residential projectdetails.."
scrapy crawl projectdetails

echo "Scrapy crawls completed."

echo "combining plotted fragmented data"
python combine-plotted.py

echo "deleting fragmented data"
rm -f developmentdetails.json
rm -f plotted.csv
rm -f projectdetails.json



echo "Plotted data processing complete!"
cd ..