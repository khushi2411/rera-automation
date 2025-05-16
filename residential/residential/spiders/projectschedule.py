import scrapy
import csv
import json
from scrapy.http import HtmlResponse

class ProjectDetailsSpider(scrapy.Spider):
    name = "projectschedule"
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
            'User-Agent': ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                           'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36'),
            'X-Requested-With': 'XMLHttpRequest',
            'sec-ch-ua': '"Not A(Brand";v="8", "Chromium";v="132", "Google Chrome";v="132"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
        }
        self.output_file = "projectschedule.json"
        self.input_file = "residential.csv"

    def load_action_ids(self):
        action_ids = []
        try:
            with open(self.input_file, "r", encoding="utf-8") as csvfile:
                reader = csv.reader(csvfile)
                next(reader, None)  # Skip header if present
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
                callback=self.parse_details,
                meta={'action_id': action_id}
            )

    def parse_details(self, response):
        """
        Extract the Internal Infrastructure, External Infrastructure, 
        and Amenities tables from the project details page.
        """
        action_id = response.meta['action_id']
        scrapy_response = HtmlResponse(url=response.url, body=response.body, encoding="utf-8")

        data = {}

        # ----------------------------
        # Extract Internal Infrastructure
        # ----------------------------
        internal_xpath = (
            '//h1[contains(text(), "Internal Infrastructure")]/following::table'
            '[contains(@class, "table-bordered")][1]/tbody/tr'
        )
        internal_rows = scrapy_response.xpath(internal_xpath)
        self.logger.info(f"Internal Infrastructure rows found: {len(internal_rows)}")
        data["InternalInfrastructure"] = self.extract_table(internal_rows, expected_columns=3)

        # ----------------------------
        # Extract External Infrastructure
        # ----------------------------
        external_xpath = (
            '//h1[contains(text(), "External Infrastructure")]/following::table'
            '[contains(@class, "table-bordered")][1]/tbody/tr'
        )
        external_rows = scrapy_response.xpath(external_xpath)
        self.logger.info(f"External Infrastructure rows found: {len(external_rows)}")
        data["ExternalInfrastructure"] = self.extract_table(external_rows, expected_columns=3)

        # ----------------------------
        # Extract Amenities
        # ----------------------------
        amenities_xpath = (
            '//h1[contains(text(), "Amenities")]/following::table'
            '[contains(@class, "table-bordered")][1]/tbody/tr'
        )
        amenities_rows = scrapy_response.xpath(amenities_xpath)
        self.logger.info(f"Amenities rows found: {len(amenities_rows)}")
        data["Amenities"] = self.extract_table(amenities_rows, expected_columns=4)

        # Save the extracted data
        self.save_to_json(action_id, data)

    def extract_table(self, rows, expected_columns):
        """
        Extract table data from a list of row selectors.
        expected_columns: number of expected columns.
        Returns a list of dictionaries.
        """
        table_data = []
        for row in rows:
            # Extract all text values from <td> tags
            cols = row.xpath('.//td/text()').getall()
            cols = [col.strip() for col in cols if col.strip()]
            row_dict = {}
            if expected_columns == 3 and len(cols) >= 3:
                row_dict["SlNo"] = cols[0]
                row_dict["Work"] = cols[1]
                row_dict["IsApplicable"] = cols[2]
            elif expected_columns == 4 and len(cols) >= 4:
                row_dict["SlNo"] = cols[0]
                row_dict["Work"] = cols[1]
                row_dict["IsApplicable"] = cols[2]
                row_dict["AreaSqM"] = cols[3]
            if row_dict:
                table_data.append(row_dict)
        return table_data

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
