import os
import json
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# ---------- Helper Functions for Persistence using JSON ----------

def load_stored_identifier(filename="C:\\Users\\khush\\scripts-rera\\stored_identifier.json"):
    """Load the stored RERA ID from a JSON file (if it exists)."""
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                return data.get("stored_identifier")
            except json.JSONDecodeError:
                print("JSON decode error. Returning None.")
                return None
    return None

def save_stored_identifier(identifier, filename="C:\\Users\\khush\\scripts-rera\\stored_identifier.json"):
    """Save the given RERA ID to a JSON file."""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump({"stored_identifier": identifier}, f, indent=4)

def save_projects_to_json(projects, filename="actionid.json"):
    """Save the projects data to a JSON file."""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(projects, f, indent=4)
    
    print(f"Wrote {len(projects)} projects to {filename}")

def format_id_from_registration(registration_number):
    """Convert registration number format from PRM/KA/RERA/1251/310/PR/030525/007705 
    to PRM_KA_RERA_1251_310_PR_030525_007705"""
    if registration_number:
        return registration_number.replace("/", "_")
    return ""

def main():
    # Load the stored identifier from file; if not found, use a default value
    stored_identifier = load_stored_identifier() or "PRM/KA/RERA/1251/310/PR/030525/007705"
    print("Loaded stored identifier:", stored_identifier)
    
    # Setup Chrome options
    options = webdriver.ChromeOptions()
    # Uncomment the following line to run Chrome headless
    # options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 10)
    
    try:
        # ------------------------------------------------------------
        # 1. Navigate to the RERA projects page
        # ------------------------------------------------------------
        URL = 'https://rera.karnataka.gov.in/viewAllProjects'
        driver.get(URL)
        print("Navigated to the RERA projects URL.")
        
        # ------------------------------------------------------------
        # 2. Set up the initial search by entering "Bengaluru Urban"
        #    in the district input field (ID: projectDist)
        # ------------------------------------------------------------
        district_input = wait.until(EC.presence_of_element_located((By.ID, "projectDist")))
        district_value = "Bengaluru Urban"
        
        # Check if the input field is read-only or disabled
        readonly_attr = district_input.get_attribute("readonly")
        if readonly_attr or not district_input.is_enabled():
            print("District input field is read-only or disabled; using JavaScript to set its value.")
            driver.execute_script("arguments[0].value = arguments[1];", district_input, district_value)
        else:
            try:
                district_input.clear()
                district_input.send_keys(district_value)
            except Exception as e:
                print("Standard method failed, falling back to JavaScript. Exception:", e)
                driver.execute_script("arguments[0].value = arguments[1];", district_input, district_value)
        print("Entered district:", district_value)
        
        # ------------------------------------------------------------
        # 3. Click the search button (assumed to have the class 'btn-style')
        # ------------------------------------------------------------
        search_button = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "btn-style")))
        search_button.click()
        print("Clicked search button.")
        
        # ------------------------------------------------------------
        # 4. Wait for the approved projects table to load (ID: approvedTable)
        # ------------------------------------------------------------
        wait.until(EC.presence_of_element_located((By.XPATH, '//table[@id="approvedTable"]')))
        print("Approved projects table loaded.")
        
        # ------------------------------------------------------------
        # 5. Trigger table sorting:
        #    a) Click the "STATUS" header once.
        #    b) Click the "APPROVED ON" header twice.
        # ------------------------------------------------------------
        status_header = wait.until(EC.element_to_be_clickable((By.XPATH, "//th[contains(text(), 'STATUS')]")))
        status_header.click()
        print("Clicked 'STATUS' header once.")
        time.sleep(2)  # Allow time for sorting animation
        
        approved_header = wait.until(EC.element_to_be_clickable((By.XPATH, "//th[contains(text(), 'APPROVED ON')]")))
        approved_header.click()
        time.sleep(2)
        approved_header.click()
        print("Clicked 'APPROVED ON' header twice.")
        time.sleep(2)
        
        # ------------------------------------------------------------
        # 6. Process pages until stored identifier is found or all pages are checked
        # ------------------------------------------------------------
        projects = []
        found_stored_identifier = False
        current_page = 1
        
        while not found_stored_identifier:
            print(f"Processing page {current_page}")
            
            # Find the index of the PROJECT TYPE column
            headers = driver.find_elements(By.XPATH, '//table[@id="approvedTable"]/thead/tr/th')
            project_type_index = None
            
            for i, header in enumerate(headers):
                if "PROJECT TYPE" in header.text:
                    project_type_index = i
                    print(f"Found PROJECT TYPE column at index {i}")
                    break
            
            # If we can't find by text, use the known index (9) based on HTML
            if project_type_index is None:
                project_type_index = 9  # based on the HTML you provided, it's the 10th column (0-indexed)
                print(f"Using default PROJECT TYPE column index: {project_type_index}")
            
            # Process all rows in the table to find action IDs and project types
            rows = driver.find_elements(By.XPATH, '//table[@id="approvedTable"]/tbody/tr')
            print(f"Total rows found on page {current_page}: {len(rows)}")
            
            for row in rows:
                cells = row.find_elements(By.TAG_NAME, "td")
                if len(cells) < 3:
                    continue  # Skip rows that do not have enough cells
                    
                # Extract the registration number
                current_rera_id = cells[2].text.strip()
                
                # Get project type if the column exists
                project_type = ""
                if project_type_index is not None and project_type_index < len(cells):
                    project_type = cells[project_type_index].text.strip()
                
                # Check if this is our stored identifier
                if current_rera_id == stored_identifier:
                    print(f"Found stored identifier: {current_rera_id} on page {current_page}. Stopping search.")
                    found_stored_identifier = True
                    break
                    
                # Find action ID links in the row
                links = row.find_elements(By.TAG_NAME, "a")
                for link in links:
                    onclick = link.get_attribute("onclick")
                    if onclick and "showFileApplicationPreview" in onclick:
                        action_id = link.get_attribute("id")
                        if action_id:
                            # Create a project entry with the formatted ID
                            formatted_id = format_id_from_registration(current_rera_id)
                            project = {
                                "id": formatted_id,
                                "action_id": action_id,
                                "RegistrationNumber": current_rera_id,
                                "ProjectType": project_type
                            }
                            projects.append(project)
                            print(f"Found new project: {current_rera_id}, id: {formatted_id}, action_id: {action_id}, type: {project_type}")
                            break
            
            # If we found the stored identifier, break out of the pagination loop
            if found_stored_identifier:
                break
                
            # Check if there's a "Next" button and if it's not disabled
            try:
                next_button = driver.find_element(By.ID, "approvedTable_next")
                # Check if the Next button is disabled or is the last page
                if "disabled" in next_button.get_attribute("class"):
                    print("Reached the last page. No more pages to check.")
                    break
                    
                # Click the "Next" button to go to the next page
                next_button.click()
                print(f"Clicked 'Next' button. Moving to page {current_page + 1}")
                current_page += 1
                
                # Wait for the table to reload with new page data
                time.sleep(3)  # Allow time for page transition
                wait.until(EC.presence_of_element_located((By.XPATH, '//table[@id="approvedTable"]')))
                
            except (NoSuchElementException, TimeoutException) as e:
                print(f"Error navigating to next page: {e}")
                break
        
        # ------------------------------------------------------------
        # 7. Update the stored identifier with the newest RERA ID
        # ------------------------------------------------------------
        if projects:
            newest_rera_id = projects[0]["RegistrationNumber"]
            save_stored_identifier(newest_rera_id)
            print(f"Stored identifier updated to: {newest_rera_id}")
        
        # ------------------------------------------------------------
        # 8. Save the project data to a JSON file
        # ------------------------------------------------------------
        if projects:
            json_filename = "C:\\Users\\khush\\scripts-rera\\actionid.json"
            save_projects_to_json(projects, json_filename)
            print(f"Latest action ID: {projects[0]['action_id']}")
            print(f"Latest formatted ID: {projects[0]['id']}")
        else:
            print("No new projects found.")
            
    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()  # Print full traceback for debugging
    finally:
        driver.quit()
        print("Browser closed.")

if __name__ == "__main__":
    main()