import scrapy
import csv
import json
from scrapy.http import HtmlResponse

class RERADevelopmentSpider(scrapy.Spider):
    name = "developmentdetails"
    start_urls = ["https://rera.karnataka.gov.in/projectDetails"]

    def __init__(self):
        # Update the session cookie as needed
        self.cookies = {'JSESSIONID': 'YOUR_SESSION_ID_HERE'}  # Replace with your actual session ID
        self.headers = {
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9,hi;q=0.8',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Origin': 'https://rera.karnataka.gov.in',
            'Referer': 'https://rera.karnataka.gov.in/projectViewDetails',
            'User-Agent': ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                           'AppleWebKit/537.36 (KHTML, like Gecko) '
                           'Chrome/132.0.0.0 Safari/537.36'),
            'X-Requested-With': 'XMLHttpRequest',
        }
        # Update the CSV path as needed
        self.input_csv = "C:\\Users\\khush\\scripts-rera\\plotted\\plotted.csv"
        self.output_file = "developmentdetails.json"
        self.extracted_results = {}  # Dictionary to store results keyed by action ID

        self.action_ids = self.load_action_ids()

    def load_action_ids(self):
        action_ids = []
        try:
            with open(self.input_csv, "r", encoding="utf-8") as csvfile:
                reader = csv.reader(csvfile)
                next(reader, None)  # Skip header
                for row in reader:
                    if row:
                        action_ids.append(row[0].strip())
        except Exception as e:
            self.logger.error(f"Error reading CSV file: {e}")
        return action_ids

    def start_requests(self):
        for action_id in self.action_ids:
            yield scrapy.FormRequest(
                url=self.start_urls[0],
                method="POST",
                headers=self.headers,
                cookies=self.cookies,
                body=f"action={action_id}",
                callback=self.parse_development_details,
                meta={'action_id': action_id}
            )

    def parse_development_details(self, response):
        action_id = response.meta['action_id']
        scrapy_response = HtmlResponse(url=response.url, body=response.text, encoding="utf-8")
        
        dev_details = {}
        
        # ----- Extract "Development Details ( Plot Dimension wise break up )" table -----
        # Use contains() to be more flexible; adjust the string if needed.
        plot_table = scrapy_response.xpath(
            "//h1[contains(., 'Development') and contains(., 'Plot Dimension wise break up')]/following::table[1]"
        )
        self.logger.info(f"[{action_id}] Found plot_table count: {len(plot_table)}")
        plot_details = []
        if plot_table:
            headers = plot_table.xpath(".//thead//th/text()").getall()
            headers = [h.strip() for h in headers if h.strip()]
            self.logger.info(f"[{action_id}] Plot table headers: {headers}")
            rows = plot_table.xpath(".//tbody//tr")
            for row in rows:
                cells = row.xpath(".//td/text()").getall()
                cells = [c.strip() for c in cells if c.strip()]
                if cells:
                    row_dict = {}
                    for i, header in enumerate(headers):
                        if i < len(cells):
                            row_dict[header] = cells[i]
                    plot_details.append(row_dict)
        else:
            self.logger.warning(f"[{action_id}] Plot table not found.")
        dev_details["Plot Details"] = plot_details

        # ----- Extract "Civil Works" table -----
        civil_table = scrapy_response.xpath(
            "//h1[contains(., 'Civil Works')]/following::table[1]"
        )
        self.logger.info(f"[{action_id}] Found civil_table count: {len(civil_table)}")
        civil_works = []
        if civil_table:
            headers = civil_table.xpath(".//thead//th/text()").getall()
            headers = [h.strip() for h in headers if h.strip()]
            self.logger.info(f"[{action_id}] Civil Works table headers: {headers}")
            rows = civil_table.xpath(".//tbody//tr")
            for row in rows:
                cells = row.xpath(".//td/text()").getall()
                cells = [c.strip() for c in cells if c.strip()]
                if cells:
                    row_dict = {}
                    for i, header in enumerate(headers):
                        if i < len(cells):
                            row_dict[header] = cells[i]
                    civil_works.append(row_dict)
        else:
            self.logger.warning(f"[{action_id}] Civil Works table not found.")
        dev_details["Civil Works"] = civil_works

        self.extracted_results[action_id] = {"Development Details": dev_details}

    def closed(self, reason):
        try:
            with open(self.output_file, "w", encoding="utf-8") as outfile:
                json.dump(self.extracted_results, outfile, indent=4, ensure_ascii=False)
            self.logger.info(f"Saved all development details to {self.output_file}")
        except Exception as e:
            self.logger.error(f"Error saving data to JSON: {e}")
