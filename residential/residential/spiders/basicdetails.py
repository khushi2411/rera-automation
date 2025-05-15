
import scrapy
import csv
import json
from scrapy.http import HtmlResponse

class RERASpider(scrapy.Spider):
    name = "basicdetails"
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
        self.input_file = "C:\\Users\\khush\\scripts-rera\\residential\\residential.csv"
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
        # You can use the response directly as it is already an HtmlResponse
        # Uncomment the line below if you want to create a new instance (usually not necessary)
        # scrapy_response = HtmlResponse(url=response.url, body=response.text, encoding="utf-8")
        scrapy_response = response

        field_dict = {}

        # ---------------------------------------------------------
        # 1) ADDITIONAL FIELDS (Project Name, Ack No, Reg No, etc.)
        # ---------------------------------------------------------
        project_name = scrapy_response.xpath('//span[contains(text(),"Project Name")]/b/text()').get(default="").strip()
        if project_name and "Project Name" not in field_dict:
            field_dict["Project Name"] = project_name

        acknowledgement_number = scrapy_response.xpath('//span[contains(text(),"Acknowledgement Number")]/b/text()').get(default="").strip()
        if acknowledgement_number and "Acknowledgement Number" not in field_dict:
            field_dict["Acknowledgement Number"] = acknowledgement_number

        registration_number = scrapy_response.xpath('//span[contains(text(),"Registration Number")]/b/text()').get(default="").strip()
        if registration_number and "Registration Number" not in field_dict:
            field_dict["Registration Number"] = registration_number

        latitude = scrapy_response.xpath('//div[p[contains(normalize-space(.),"Latitude")]]/following-sibling::div[1]/p/text()').get(default="").strip()
        if latitude and "Latitude" not in field_dict:
            field_dict["Latitude"] = latitude

        longitude = scrapy_response.xpath('//div[p[contains(normalize-space(.),"Longitude")]]/following-sibling::div[1]/p/text()').get(default="").strip()
        if longitude and "Longitude" not in field_dict:
            field_dict["Longitude"] = longitude

        local_authority = scrapy_response.xpath('//div[p[contains(normalize-space(.),"Local Authority")]]/following-sibling::div[1]/p/text()').get(default="").strip()
        if local_authority and "Local Authority" not in field_dict:
            field_dict["Local Authority"] = local_authority

        # ---------------------------------------------------------
        # 2) EXISTING LOGIC (FIELD MAPPING)
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
            'Is TDR Applicable ?': 'Is TDR Applicable ?',
        }

       
        for nodes in [project_details_nodes, inventory_details_nodes, taluk_details_nodes]:
            for i in range(len(nodes)):
                label = nodes[i].xpath('normalize-space(text())').get(default="").strip()
                value = (nodes[i+1].xpath('normalize-space(text())').get(default="").strip() if i + 1 < len(nodes) else "")
                if label and label in field_mapping:
                    mapped_label = field_mapping[label]
                    if mapped_label not in field_dict:
                        field_dict[mapped_label] = value

        # ---------------------------------------------------------
        # 3) Store the extracted data in the results list
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
