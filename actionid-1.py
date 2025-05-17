import os
import json
import time
import asyncio
from playwright.async_api import async_playwright, TimeoutError

# ---------- Helper Functions for Persistence using JSON ----------

def load_stored_identifier(filename="./utils/stored_identifier.json"):
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

def save_stored_identifier(identifier, filename="./utils/stored_identifier.json"):
    """Save the given RERA ID to a JSON file."""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump({"stored_identifier": identifier}, f, indent=4)

def save_projects_to_json(projects, filename="./utils/actionid.json"):
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

async def main():
    # Load the stored identifier from file; if not found, use a default value
    stored_identifier = load_stored_identifier() or "PRM/KA/RERA/1251/310/PR/030525/007705"
    print("Loaded stored identifier:", stored_identifier)
    
    # Configure browser options
    browser_args = [
        '--disable-web-security',
        '--disable-features=IsolateOrigins,site-per-process',
        '--disable-site-isolation-trials',
        '--disable-features=BlockInsecurePrivateNetworkRequests',
        '--disable-blink-features=AutomationControlled',
        '--disable-dev-shm-usage',  # Helps in Docker environments
        '--no-sandbox',  # Helps in restricted environments
    ]
    
    async with async_playwright() as p:
        # Launch browser with custom arguments
       browser = p.chromium.launch(
        proxy={
            "server": "socks5://localhost:9090",
        }
    )
        
        # Create a context with custom settings
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080},
            ignore_https_errors=True
        )
        
        # Enable request interception for better debugging
        await context.route('**/*', lambda route: route.continue_())
        
        page = await context.new_page()
        
        try:
            # ------------------------------------------------------------
            # 1. Navigate to the RERA projects page with increased timeout
            # ------------------------------------------------------------
            URL = 'https://rera.karnataka.gov.in/viewAllProjects'
            print(f"Attempting to navigate to {URL} with extended timeout...")
            
            try:
                # Try with a longer timeout (90 seconds)
                await page.goto(URL, timeout=90000, wait_until='domcontentloaded')
                print("Successfully navigated to the RERA projects URL.")
            except TimeoutError as e:
                print(f"Page load timed out even with extended timeout: {e}")
                print("Taking screenshot of current page state...")
                await page.screenshot(path="timeout_screenshot.png")
                print("Screenshot saved to timeout_screenshot.png")
                
                # Check if we can still interact with the page
                current_url = page.url
                print(f"Current URL: {current_url}")
                page_content = await page.content()
                print(f"Page content length: {len(page_content)} characters")
                
                # If page content is very short, we probably failed to load anything useful
                if len(page_content) < 1000:
                    print("Page content too short, assuming failed load.")
                    raise Exception("Failed to load the page properly.")
                
                print("Continuing with caution as page might have partially loaded...")
            
            # ------------------------------------------------------------
            # 2. Wait for page to stabilize and check if we need to retry
            # ------------------------------------------------------------
            await page.wait_for_timeout(5000)  # Wait 5 seconds for any scripts to run
            
            # Check if the district input exists
            district_input = await page.query_selector('#projectDist')
            if not district_input:
                print("District input field not found! Taking screenshot...")
                await page.screenshot(path="missing_input_field.png")
                
                # Attempt to reload the page
                print("Attempting to reload the page...")
                await page.reload(timeout=90000, wait_until='domcontentloaded')
                await page.wait_for_timeout(5000)
                
                # Check again for the district input
                district_input = await page.query_selector('#projectDist')
                if not district_input:
                    print("Still can't find district input after reload. Aborting.")
                    raise Exception("Required elements not found on page.")
            
            # ------------------------------------------------------------
            # 2. Set up the initial search by entering "Bengaluru Urban"
            # ------------------------------------------------------------
            district_value = "Bengaluru Urban"
            
            # Set the value using JavaScript
            await page.evaluate(f'document.getElementById("projectDist").value = "{district_value}"')
            print("Entered district:", district_value)
            
            # ------------------------------------------------------------
            # 3. Click the search button
            # ------------------------------------------------------------
            print("Looking for search button...")
            search_button = await page.query_selector('.btn-style')
            
            if not search_button:
                print("Search button not found with .btn-style. Looking for alternatives...")
                # Try alternative selectors
                search_button = await page.query_selector('button[type="submit"]')
                if not search_button:
                    search_button = await page.query_selector('input[type="submit"]')
                if not search_button:
                    # Look for any button with text containing 'search'
                    search_button = await page.query_selector('button:has-text("Search")')
                
                if not search_button:
                    print("Cannot find search button. Taking screenshot...")
                    await page.screenshot(path="missing_search_button.png")
                    raise Exception("Search button not found")
            
            await search_button.click()
            print("Clicked search button.")
            
            # Wait longer for the results to load
            await page.wait_for_timeout(10000)  # Wait 10 seconds
            
            # ------------------------------------------------------------
            # 4. Wait for the approved projects table to load
            # ------------------------------------------------------------
            try:
                await page.wait_for_selector('table#approvedTable', timeout=60000)
                print("Approved projects table loaded.")
            except TimeoutError:
                print("Table failed to load. Taking screenshot...")
                await page.screenshot(path="table_load_failed.png")
                
                # Check if there's any error message
                error_message = await page.query_selector('div.error-message')
                if error_message:
                    error_text = await error_message.inner_text()
                    print(f"Error message found: {error_text}")
                
                # Try to debug what's on the page
                page_html = await page.content()
                with open("page_debug.html", "w", encoding="utf-8") as f:
                    f.write(page_html)
                print("Saved current page HTML to page_debug.html")
                
                raise Exception("Table did not load within timeout period")
            
            # ------------------------------------------------------------
            # 5. Trigger table sorting:
            #    a) Click the "STATUS" header once.
            #    b) Click the "APPROVED ON" header twice.
            # ------------------------------------------------------------
            try:
                await page.click("th:has-text('STATUS')")
                print("Clicked 'STATUS' header once.")
                await page.wait_for_timeout(3000)  # Wait for 3 seconds
                
                await page.click("th:has-text('APPROVED ON')")
                await page.wait_for_timeout(3000)
                await page.click("th:has-text('APPROVED ON')")
                print("Clicked 'APPROVED ON' header twice.")
                await page.wait_for_timeout(3000)
            except Exception as e:
                print(f"Error during table sorting: {e}")
                print("Continuing anyway as this is not critical...")
            
            # ------------------------------------------------------------
            # 6. Process pages until stored identifier is found or all pages are checked
            # ------------------------------------------------------------
            projects = []
            found_stored_identifier = False
            current_page = 1
            
            while not found_stored_identifier:
                print(f"Processing page {current_page}")
                
                # Find the index of the PROJECT TYPE column
                headers = await page.query_selector_all('table#approvedTable thead tr th')
                project_type_index = None
                
                for i, header in enumerate(headers):
                    header_text = await header.inner_text()
                    if "PROJECT TYPE" in header_text:
                        project_type_index = i
                        print(f"Found PROJECT TYPE column at index {i}")
                        break
                
                # If we can't find by text, use the known index based on HTML
                if project_type_index is None:
                    project_type_index = 9  # based on the HTML you provided
                    print(f"Using default PROJECT TYPE column index: {project_type_index}")
                
                # Process all rows in the table
                rows = await page.query_selector_all('table#approvedTable tbody tr')
                print(f"Total rows found on page {current_page}: {len(rows)}")
                
                for row in rows:
                    cells = await row.query_selector_all('td')
                    if len(cells) < 3:
                        continue  # Skip rows that do not have enough cells
                        
                    # Extract the registration number
                    current_rera_id = await cells[2].inner_text()
                    current_rera_id = current_rera_id.strip()
                    
                    # Get project type if the column exists
                    project_type = ""
                    if project_type_index is not None and project_type_index < len(cells):
                        project_type = await cells[project_type_index].inner_text()
                        project_type = project_type.strip()
                    
                    # Check if this is our stored identifier
                    if current_rera_id == stored_identifier:
                        print(f"Found stored identifier: {current_rera_id} on page {current_page}. Stopping search.")
                        found_stored_identifier = True
                        break
                        
                    # Find action ID links in the row
                    links = await row.query_selector_all('a')
                    for link in links:
                        onclick = await link.get_attribute('onclick')
                        if onclick and "showFileApplicationPreview" in onclick:
                            action_id = await link.get_attribute('id')
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
                next_button = await page.query_selector('#approvedTable_next')
                if next_button:
                    # Check if the Next button is disabled
                    next_button_class = await next_button.get_attribute('class')
                    if next_button_class and "disabled" in next_button_class:
                        print("Reached the last page. No more pages to check.")
                        break
                        
                    # Click the "Next" button to go to the next page
                    await next_button.click()
                    print(f"Clicked 'Next' button. Moving to page {current_page + 1}")
                    current_page += 1
                    
                    # Wait for the table to reload with new page data
                    await page.wait_for_timeout(5000)  # Wait for 5 seconds
                    try:
                        await page.wait_for_selector('table#approvedTable:not(.processing)', timeout=30000)
                    except:
                        print("Waited for table processing to complete, continuing anyway...")
                    
                else:
                    print("Next button not found. Assuming this is the last page.")
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
                json_filename = "./utils/actionid.json"
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
            await browser.close()
            print("Browser closed.")

if __name__ == "__main__":
    asyncio.run(main())
