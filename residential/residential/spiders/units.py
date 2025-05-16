import scrapy
import csv
import json
from scrapy.http import HtmlResponse

class UnitDetailsSpider(scrapy.Spider):
    name = "units"
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
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
                          '(KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36',
            'X-Requested-With': 'XMLHttpRequest',
            'sec-ch-ua': '"Not A(Brand";v="8", "Chromium";v="132", "Google Chrome";v="132"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
        }

        self.input_file = "residential.csv"
        self.output_file = "unit_details.json"

    def load_action_ids(self):
        action_ids = []
        try:
            with open(self.input_file, "r", encoding="utf-8") as csvfile:
                reader = csv.reader(csvfile)
                next(reader, None)
                for row in reader:
                    if row:
                        action_ids.append(row[0])
        except FileNotFoundError:
            self.logger.error(f"Input file '{self.input_file}' not found.")
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
                callback=self.parse_unit_table,
                meta={'action_id': action_id}
            )

    def parse_unit_table(self, response):
        action_id = response.meta['action_id']
        scrapy_response = HtmlResponse(url=response.url, body=response.body, encoding="utf-8")

        unit_table = scrapy_response.xpath('//table[@class="table table-bordered table-striped table-condensed"]'
                                           '[.//th[contains(text(),"Sl No")] '
                                           'and .//th[contains(text(),"Floor No")] '
                                           'and .//th[contains(text(),"Unit No")]]')

        if not unit_table:
            self.logger.warning(f"No matching unit details table found for Action ID {action_id}")
            self.save_to_json(action_id, [])
            return

        all_tables = []  # To store separate tables
        current_table = []  # Holds the current active table

        rows = unit_table.xpath('.//tbody/tr')

        for row in rows:
            columns = row.xpath('./td/text()').extract()
            if len(columns) == 9:
                unit_entry = {
                    "Sl No": columns[0].strip(),
                    "Floor No": columns[1].strip(),
                    "Unit No": columns[2].strip(),
                    "Unit Type": columns[3].strip(),
                    "Carpet Area": columns[4].strip(),
                    "Exclusive Common Area Allottee": columns[5].strip(),
                    "Common Area Alloted To Association": columns[6].strip(),
                    "Undivided Share": columns[7].strip(),
                    "No of parking lots": columns[8].strip(),
                }

                # If "Sl No" is 1, start a new table
                if unit_entry["Sl No"] == "1" and current_table:
                    all_tables.append(current_table)
                    current_table = []

                current_table.append(unit_entry)

        # Append last table if it has data
        if current_table:
            all_tables.append(current_table)

        self.save_to_json(action_id, all_tables)

    def save_to_json(self, action_id, unit_data):
        try:
            try:
                with open(self.output_file, "r", encoding="utf-8") as infile:
                    existing_data = json.load(infile)
            except (FileNotFoundError, json.JSONDecodeError):
                existing_data = {}

            existing_data[action_id] = unit_data  # Save as a list of lists (separate tables)

            with open(self.output_file, "w", encoding="utf-8") as outfile:
                json.dump(existing_data, outfile, indent=4, ensure_ascii=False)

            self.logger.info(f"Saved unit details for Action ID {action_id} to '{self.output_file}'")
        except Exception as e:
            self.logger.error(f"Error saving unit details for Action ID {action_id}: {e}")