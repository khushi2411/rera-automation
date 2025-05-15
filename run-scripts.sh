set -e


echo "scraping actionids"
python actionid-1.py

echo "converting actionids to csv"
python json-to-csv-2.py

echo "deleting actionid.json"
rm -f './utils/actionid.json'


echo "Running residential shell scripts..."
bash "./residential/run-residential-scripts.sh"

echo "Running plotted shell scripts..."
bash './plotted/run-plotted-scripts.sh'

echo "Shell scripts completed."



echo "Running plotted upload script"
node update-plotted.js

echo "Running residentail upload script"
node update-residential.js



echo "Deleting final merged files after upload"
rm -f './residential/final-rera-residential.json'
rm -f './plotted/final-rera-plotted.json'

echo "All tasks completed successfully!"