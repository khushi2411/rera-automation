import scrapy
import csv
import json
from scrapy.http import HtmlResponse

class FloorPlanSpider(scrapy.Spider):
    name = "floorplan"
    start_urls = ["https://rera.karnataka.gov.in/projectDetails"]  # Adjust if needed

    def __init__(self):
        # Replace these with valid session cookies and request headers for your environment
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

        # CSV file with action IDs and JSON output
        self.input_file = "C:\\Users\\khush\\scripts-rera\\residential\\residential.csv"
        self.output_file = "floorplan.json"

    def load_action_ids(self):
        """Reads the first column from 'extracted_action_ids_stream.csv' as action IDs."""
        action_ids = []
        try:
            with open(self.input_file, "r", encoding="utf-8") as csvfile:
                reader = csv.reader(csvfile)
                next(reader, None)  # Skip header row if present
                for row in reader:
                    if row:
                        action_ids.append(row[0])
        except FileNotFoundError:
            self.logger.error(f"Input file '{self.input_file}' not found.")
        return action_ids

    def start_requests(self):
        """
        Sends a POST request for each action_id, 
        with 'body=f\"action={action_id}\"' to projectDetails.
        """
        action_ids = self.load_action_ids()
        for action_id in action_ids:
            yield scrapy.Request(
                url=self.start_urls[0],
                method="POST",
                headers=self.headers,
                cookies=self.cookies,
                body=f"action={action_id}",
                callback=self.parse_floor_plan,
                meta={'action_id': action_id}
            )

    def parse_floor_plan(self, response):
        """
        Looks for all matching floor-plan tables, loops over each,
        extracts floor number & no. of units from each row, 
        and saves them in a list of lists into floorplan.json
        """
        action_id = response.meta['action_id']
        scrapy_response = HtmlResponse(url=response.url, body=response.body, encoding="utf-8")

        # Locate *all* tables with the 'Floor No' / 'No of Units' heading
        floor_tables = scrapy_response.xpath(
            '//table[@class="table table-bordered table-striped table-condensed"]'
            '[.//th[@colspan="5" and contains(text(),"Floor No")] '
            ' and .//th[@colspan="4" and contains(text(),"No of Units")]]'
        )

        if not floor_tables:
            self.logger.warning(f"No matching floor plan table found for Action ID {action_id}")
            self.save_to_json(action_id, [])
            return

        all_tables_data = []  # This will hold a list of lists

        for table in floor_tables:
            # Identify the row that has the <th colspan="5">Floor No</th>, etc.
            floor_heading = table.xpath(
                './/tr[th[@colspan="5" and contains(text(),"Floor No")] and '
                '     th[@colspan="4" and contains(text(),"No of Units")]]'
            )
            if not floor_heading:
                self.logger.info(f"No floor header row in this table. Skipping. (Action ID {action_id})")
                continue

            # Next, get the subsequent <tr> from either a <tbody> or direct siblings
            floor_rows = floor_heading.xpath('./following-sibling::tbody[1]/tr')
            if not floor_rows:
                floor_rows = floor_heading.xpath('./following-sibling::tr')

            table_data = []
            for row in floor_rows:
                # If we see a <th> row, we assume it's a heading or new table => stop reading more rows
                if row.xpath('./th'):
                    break

                floor_no = row.xpath('./td[1]/text()').get()
                no_of_units = row.xpath('./td[2]/text()').get()

                # Typically the row has <td colspan="5">someFloor</td><td colspan="4">someUnits</td>
                if floor_no and no_of_units:
                    table_data.append({
                        "FloorNo": floor_no.strip(),
                        "NoOfUnits": no_of_units.strip()
                    })
                else:
                    # Possibly a filler/heading row or incomplete data => break
                    break

            if table_data:
                all_tables_data.append(table_data)

        # Save the combined multi-table data
        self.save_to_json(action_id, all_tables_data)

    def save_to_json(self, action_id, all_floor_data):
        """
        Loads 'floorplan.json' from disk, merges/updates data for the current action_id,
        then writes back. all_floor_data is a list of lists, e.g. [ [ {FloorNo,NoOfUnits},.. ], ... ]
        """
        try:
            try:
                with open(self.output_file, "r", encoding="utf-8") as infile:
                    existing_data = json.load(infile)
            except (FileNotFoundError, json.JSONDecodeError):
                existing_data = {}

            existing_data[action_id] = all_floor_data

            with open(self.output_file, "w", encoding="utf-8") as outfile:
                json.dump(existing_data, outfile, indent=4, ensure_ascii=False)

            self.logger.info(f"Saved floor plan data for Action ID {action_id} to '{self.output_file}'")
        except Exception as e:
            self.logger.error(f"Error saving floor plan data for Action ID {action_id}: {e}")
