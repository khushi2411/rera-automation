import scrapy
import csv
import json
from scrapy.http import HtmlResponse

class RERASpider(scrapy.Spider):
    name = "towers"
    start_urls = ["https://rera.karnataka.gov.in/projectDetails"]

    def __init__(self):
        self.cookies = {
            'JSESSIONID': 'F474E2915CE022928A5A77CCA69C5CC8',
        }
        self.headers = {
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Origin': 'https://rera.karnataka.gov.in',
            'Referer': 'https://rera.karnataka.gov.in/projectViewDetails',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36',
            'X-Requested-With': 'XMLHttpRequest',
            'sec-ch-ua': '"Not A(Brand";v="8", "Chromium";v="132", "Google Chrome";v="132"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
        }
        self.output_file = "tower_data.json"
        self.input_file = "C:\\Users\\khush\\scripts-rera\\residential\\residential.csv"

    def load_action_ids(self):
        action_ids = []
        try:
            with open(self.input_file, "r", encoding="utf-8") as csvfile:
                reader = csv.reader(csvfile)
                next(reader, None)  # Skip the header row
                for row in reader:
                    if row:
                        action_ids.append(row[0])
        except FileNotFoundError:
            self.logger.error(f"Input file {self.input_file} not found.")
        return action_ids

    def start_requests(self):
        action_ids = self.load_action_ids()
        for action_id in action_ids:
            yield scrapy.Request(
                url=self.start_urls[0],
                method="POST",
                headers=self.headers,
                cookies=self.cookies,
                body=f"action={action_id}",
                callback=self.parse_tower_data,
                meta={'action_id': action_id}
            )

    def parse_tower_data(self, response):
        action_id = response.meta['action_id']
        scrapy_response = HtmlResponse(url=response.url, body=response.body, encoding="utf-8")
        
        # Only the keys you want
        desired_keys = [
            "Tower Name", "Type", "No. of Floors", "Total No. of Units",
            "No. of Stilts", "No. of slab of super structure",
            "No. of Basement", "Total No. of Parking",
            "Height of the Tower (In Meters)"
        ]
        
        # Prepare our data dictionary
        data = {
            "TowerDetails": []
        }
        
        # Select all tables that match these headers
        tower_tables = scrapy_response.xpath('//table[contains(., "Tower Name") and contains(., "No. of Floors")]')
        
        if not tower_tables:
            self.logger.warning(f"No tower details table found for Action ID {action_id}")
        else:
            for t_index, tower_table in enumerate(tower_tables, start=1):
                # We create a dictionary for the current tower
                tower_dict = {}
                rows = tower_table.xpath('.//tr')

                for row in rows:
                    texts = row.xpath('.//text()').getall()
                    texts = [t.strip() for t in texts if t.strip()]
                    # Pair the texts: first = key, second = value
                    for i in range(0, len(texts), 2):
                        if i + 1 < len(texts):
                            key = texts[i]
                            value = texts[i + 1]
                            if key in desired_keys:
                                tower_dict[key] = value
                
                # If this table provided any data, add it to the list of towers
                if tower_dict:
                    data["TowerDetails"].append(tower_dict)

        # Save combined tower data for this action_id
        self.save_to_json(action_id, data)

    def save_to_json(self, action_id, data):
        try:
            try:
                with open(self.output_file, "r", encoding="utf-8") as infile:
                    existing_data = json.load(infile)
            except (FileNotFoundError, json.JSONDecodeError):
                existing_data = {}

            existing_data[action_id] = data
            with open(self.output_file, "w", encoding="utf-8") as outfile:
                json.dump(existing_data, outfile, indent=4, ensure_ascii=False)

            self.logger.info(f"Saved data for Action ID {action_id} to {self.output_file}")
        except Exception as e:
            self.logger.error(f"Error saving data: {e}")
