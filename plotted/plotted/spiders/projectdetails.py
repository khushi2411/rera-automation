import scrapy
import csv
import json
from scrapy.http import HtmlResponse

class RERASpider(scrapy.Spider):
    name = "projectdetails"
    start_urls = ["https://rera.karnataka.gov.in/projectDetails"]

    def __init__(self):
        self.cookies = {'JSESSIONID': '02E62E6483634774FB712EBE28E64DEC'}  # Update as needed
        self.headers = {
            'Accept': 'application/xml, text/xml, */*; q=0.01',
            'Accept-Language': 'en-US,en;q=0.9',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Origin': 'https://rera.karnataka.gov.in',
            'Referer': 'https://rera.karnataka.gov.in/projectViewDetails',
            'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                           'AppleWebKit/537.36 (KHTML, like Gecko) '
                           'Chrome/131.0.0.0 Safari/537.36'),
            'X-Requested-With': 'XMLHttpRequest',
        }
        self.input_file = "plotted.csv"
        self.output_file = "projectdetails.json"
        self.extracted_results = []  # List to store results

        # Read action IDs from input CSV
        self.action_ids = self.load_action_ids()

    def load_action_ids(self):
        """Loads action IDs from CSV."""
        action_ids = []
        try:
            with open(self.input_file, "r", encoding="utf-8") as infile:
                reader = csv.reader(infile)
                next(reader, None)  # Skip header
                for row in reader:
                    if row:
                        action_ids.append(row[0])
        except FileNotFoundError:
            self.logger.error(f"File {self.input_file} not found.")
        return action_ids

    def start_requests(self):
        for action_id in self.action_ids:
            yield scrapy.FormRequest(
                url=self.start_urls[0],
                formdata={'action': action_id},
                cookies=self.cookies,
                headers=self.headers,
                callback=self.parse_project_details,
                meta={'action_id': action_id}
            )

    def parse_project_details(self, response):
        action_id = response.meta['action_id']
        scrapy_response = response

        field_dict = {}

        # ---------------------------------------------------------
        # 1) Parse major fields (Project Name, Acknowledgement Number, etc.)
        # ---------------------------------------------------------
        project_name = scrapy_response.xpath('//span[contains(text(),"Project Name")]/b/text()').get(default="").strip()
        if project_name:
            field_dict["Project Name"] = str(project_name)

        acknowledgement_number = scrapy_response.xpath('//span[contains(text(),"Acknowledgement Number")]/b/text()').get(default="").strip()
        if acknowledgement_number:
            field_dict["Acknowledgement Number"] = str(acknowledgement_number)

        registration_number = scrapy_response.xpath('//span[contains(text(),"Registration Number")]/b/text()').get(default="").strip()
        if registration_number:
            field_dict["Registration Number"] = str(registration_number)

        latitude = scrapy_response.xpath('//div[p[contains(normalize-space(.),"Latitude")]]/following-sibling::div[1]/p/text()').get(default="").strip()
        if latitude:
            field_dict["Latitude"] = str(latitude)

        longitude = scrapy_response.xpath('//div[p[contains(normalize-space(.),"Longitude")]]/following-sibling::div[1]/p/text()').get(default="").strip()
        if longitude:
            field_dict["Longitude"] = str(longitude)

        local_authority = scrapy_response.xpath('//div[p[contains(normalize-space(.),"Local Authority")]]/following-sibling::div[1]/p/text()').get(default="").strip()
        if local_authority:
            field_dict["Local Authority"] = str(local_authority)

        # ---------------------------------------------------------
        # 2) EXISTING LOGIC: Map additional fields via common labels
        # ---------------------------------------------------------
        project_details_nodes = scrapy_response.xpath('//div[@class="col-md-3 col-sm-6 col-xs-6"]/p')
        taluk_details_nodes = scrapy_response.xpath('//div[@class="col-md-6 col-sm-6 col-xs-6"]/p')
        inventory_details_nodes = scrapy_response.xpath('//div[@class="col-md-3 col-sm-6 col-xs-6"]/p')

        field_mapping = {
            'Project Name': 'Project Name',
            'Project Description': 'Project Description',
            'Project Type': 'Project Type',
            'Project Status': 'Project Status',
            'Project Sub Type': 'Project Sub Type',
            'Total amount of money used for development of project': 'Total amount of money used for development of project',
            'Extent of development carried till date': 'Extent of development carried till date',
            'Extent of development pending': 'Extent of development pending',
            'Project Start Date': 'Project Start Date',
            'Proposed Completion Date': 'Proposed Completion Date',
            'Project Address': 'Project Address',
            'District': 'District',
            'Taluk': 'Taluk',
            'Pin Code': 'Pin Code',
            'North Schedule': 'North Schedule',
            'East Schedule': 'East Schedule',
            'South Schedule': 'South Schedule',
            'West Schedule': 'West Schedule',
            'Approving Authority': 'Approving Authority',
            'Approved Plan Number': 'Approved Plan Number',
            'Plan Approval Date': 'Plan Approval Date',
            'Have you applied for RERA Registration for the same Plan ?': 'Have you applied for RERA Registration for the same Plan ?',
            'Total Number of Inventories/Flats/Villas': 'Total Number of Inventories/Flats/Villas',
            'No. of Open Parking': 'No. of Open Parking',
            'No. of Garage': 'No. of Garage',
            'No. of Covered Parking': 'No. of Covered Parking',
            'Total Open Area (Sq Mtr) (A1)': 'Total Open Area (Sq Mtr) (A1)',
            'Total Area Of Land (Sq Mtr) (A1+A2)': 'Total Area Of Land (Sq Mtr) (A1+A2)',
            'Total Built-up Area of all the Floors (Sq Mtr)': 'Total Built-up Area of all the Floors (Sq Mtr)',
            'Total Plinth Area (Sq Mtr)': 'Total Plinth Area (Sq Mtr)',
            'Area Of Open Parking (Sq Mtr)': 'Area Of Open Parking (Sq Mtr)',
            'Area of Garage (Sq Mtr)': 'Area of Garage (Sq Mtr)',
            'Total Coverd Area (Sq Mtr) (A2)': 'Total Coverd Area (Sq Mtr) (A2)',
            'Total Carpet Area of all the Floors (Sq Mtr)': 'Total Carpet Area of all the Floors (Sq Mtr)',
            'Area Of Covered Parking (Sq Mtr)': 'Area Of Covered Parking (Sq Mtr)',
            'Source of Water': 'Source of Water',
        }

        for nodes in [project_details_nodes, inventory_details_nodes, taluk_details_nodes]:
            for i in range(len(nodes)):
                label = nodes[i].xpath('normalize-space(text())').get(default="").strip()
                value = ""
                if i + 1 < len(nodes):
                    value = nodes[i+1].xpath('normalize-space(text())').get(default="").strip()
                if label and label in field_mapping:
                    mapped_label = field_mapping[label]
                    if mapped_label not in field_dict:
                        field_dict[mapped_label] = str(value)

        # ---------------------------------------------------------
        # 3) PARSE THE "LANDUSE ANALYSIS" SECTION
        #    Only extract specific keys in a flat dictionary.
        # ---------------------------------------------------------
        wanted_keys = [
            "Total Number of Sites/Plots",
            "Total Covered Area (Residential or Commercial)",
            "Total Number of Parks and open spaces",
            "Total Area of Parks and Open Spaces",
            "Total Number of CA Sites",
            "Total Area of CA Sites",
            "Total Area of Roads",
            "Total Open Area (Parks and open spaces, CA sites, Roads, public utilities)",
            "Total Area Land"
        ]
        landuse_analysis = {}
        # Select rows in the Landuse Analysis table using a flexible XPath
        landuse_rows = scrapy_response.xpath('//table[contains(@class,"table-condensed")]//tr')
        self.logger.info(f"[{action_id}] Found {len(landuse_rows)} landuse table rows")
        for row in landuse_rows:
            cells = row.xpath('./td//text()').getall()
            cells = [str(c.strip()) for c in cells if c.strip()]
            self.logger.info(f"[{action_id}] Landuse row cells: {cells}")
            # If the row has 5 cells, assume two key-value pairs:
            if len(cells) >= 5:
                key1 = cells[0]
                value1 = cells[1]
                key2 = cells[2]
                value2 = cells[4]
                if key1 in wanted_keys:
                    landuse_analysis[key1] = value1
                if key2 in wanted_keys:
                    landuse_analysis[key2] = value2
            # If the row has exactly 3 cells, assume one key-value pair:
            elif len(cells) == 3:
                key = cells[0]
                value = cells[2]
                if key in wanted_keys:
                    landuse_analysis[key] = value
        if landuse_analysis:
            field_dict["Landuse Analysis"] = landuse_analysis
        else:
            self.logger.info(f"[{action_id}] No Landuse Analysis data found.")

        # ---------------------------------------------------------
        # 4) Store the extracted data in the results list
        # ---------------------------------------------------------
        result = {"ActionID": action_id, "Details": field_dict}
        self.extracted_results.append(result)
        self.logger.info(f"Saved Action ID {action_id}")

    def closed(self, reason):
        """Write all extracted results to JSON file when spider closes."""
        try:
            with open(self.output_file, "w", encoding="utf-8") as outfile:
                json.dump(self.extracted_results, outfile, ensure_ascii=False, indent=4)
            self.logger.info(f"Saved all data to {self.output_file}")
        except Exception as e:
            self.logger.error(f"Error saving data to JSON: {e}")
