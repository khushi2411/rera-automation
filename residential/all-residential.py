import json
import os
import re

def format_id_from_registration(registration_number):
    """Convert registration number format from PRM/KA/RERA/1251/310/PR/030525/007705 
    to PRM_KA_RERA_1251_310_PR_030525_007705"""
    if registration_number and isinstance(registration_number, str):
        return registration_number.replace("/", "_")
    return ""

# Helper function to load JSON from a file with error handling
def load_json(filename):
    try:
        with open(filename, 'r') as f:
            data = json.load(f)
            print(f"Successfully loaded {filename}, type: {type(data)}")
            return data
    except FileNotFoundError:
        print(f"Warning: File {filename} not found.")
        return {}
    except json.JSONDecodeError as e:
        print(f"Warning: Error decoding JSON in {filename}: {e}")
        return {}

# File paths with full paths

project_details_path =  "projectdetails.json"
project_schedule_path = "projectschedule.json"
inventory_path =  "inventory.json"
tower_data_path =  "tower_data.json"
floorplan_path = "floorplan.json"
unit_details_path =  "unit_details.json"

# Load each JSON file
project_details = load_json(project_details_path)
project_schedule = load_json(project_schedule_path)
inventory = load_json(inventory_path)
tower_data = load_json(tower_data_path)
floorplan = load_json(floorplan_path)
unit_details = load_json(unit_details_path)

# Get a set of all unique keys (project IDs) from all files
all_keys = set()

# Add keys from each dictionary, handling different data types
for name, data in [
    ("project_details", project_details),
    ("project_schedule", project_schedule),
    ("inventory", inventory),
    ("tower_data", tower_data),
    ("floorplan", floorplan),
    ("unit_details", unit_details)
]:
    if isinstance(data, dict):
        all_keys.update(data.keys())
        print(f"Added {len(data.keys())} keys from {name}")
    elif isinstance(data, list):
        # If the data is a list, check if it's a list of dictionaries
        print(f"Warning: {name} is a list, not a dictionary.")
        if data and isinstance(data[0], dict) and "ActionID" in data[0]:
            # For data like in paste.txt where we have a list of objects with ActionID
            for item in data:
                if "ActionID" in item:
                    all_keys.add(item["ActionID"])
            print(f"Extracted {len(data)} ActionIDs from list in {name}")
    else:
        print(f"Warning: {name} has unexpected type: {type(data)}")

print(f"Found {len(all_keys)} unique project keys.")

# Prepare the final consolidated list of projects
all_projects = []

for key in all_keys:
    combined_project = {}
    registration_number = None
    
    # Merge project details if available (handling both dictionary and list formats)
    if isinstance(project_details, dict) and key in project_details:
        details_data = project_details[key]
        combined_project.update(details_data)
        
        # Extract registration number if available
        if "Registration Number" in details_data:
            registration_number = details_data["Registration Number"]
        elif "RegistrationNumber" in details_data:
            registration_number = details_data["RegistrationNumber"]
    elif isinstance(project_details, list):
        # For data like in paste.txt
        for item in project_details:
            if item.get("ActionID") == key:
                if "Details" in item:
                    combined_project["Details"] = item["Details"]
                    # Look for registration number in Details
                    if "Registration Number" in item["Details"]:
                        registration_number = item["Details"]["Registration Number"]
                    elif "RegistrationNumber" in item["Details"]:
                        registration_number = item["Details"]["RegistrationNumber"]
                else:
                    combined_project.update(item)
                break
    
    # Merge project schedule if available
    if isinstance(project_schedule, dict) and key in project_schedule:
        combined_project.update(project_schedule[key])
    
    # Add inventory list under the key "inventory"
    if isinstance(inventory, dict) and key in inventory:
        combined_project["inventory"] = inventory[key]
    
    # Process tower data, floorplan, and unit details together
    tower_details_for_key = []
    floorplans_for_key = []
    unit_details_for_key = []
    
    # Get tower data for this key
    if isinstance(tower_data, dict) and key in tower_data:
        if "TowerDetails" in tower_data[key]:
            tower_details_for_key = tower_data[key]["TowerDetails"]
        else:
            tower_details_for_key = tower_data[key]
    
    # Get floorplan data for this key
    if isinstance(floorplan, dict) and key in floorplan:
        floorplans_for_key = floorplan[key]
    
    # Get unit details data for this key
    if isinstance(unit_details, dict) and key in unit_details:
        unit_details_for_key = unit_details[key]
    elif isinstance(unit_details, list):
        # This is for handling the nested array structure in unit_details
        # where the first element might be the project key
        unit_details_for_key = unit_details
    
    # Process tower, floorplan and units data together if available
    if tower_details_for_key:
        towers = []
        
        # For each tower
        for i, tower in enumerate(tower_details_for_key):
            # Create a tower object
            tower_obj = dict(tower)
            
            # Add floorplan if available for this tower
            if i < len(floorplans_for_key):
                tower_obj["floorplan"] = floorplans_for_key[i]
            
            # Add unit details if available for this tower
            # If unit_details are nested (array within array), get the correct one
            if isinstance(unit_details_for_key, list) and len(unit_details_for_key) > 0:
                if (isinstance(unit_details_for_key[0], list) and i < len(unit_details_for_key)):
                    # For formats like [ [ {...}, {...} ], [ {...}, {...} ] ]
                    tower_obj["units"] = unit_details_for_key[i] if i < len(unit_details_for_key) else []
                else:
                    # For flat list of units, assign all to the first tower
                    # This is a simplification; you might need a more sophisticated approach
                    # to match units to towers based on tower names or other criteria
                    if i == 0:
                        tower_obj["units"] = unit_details_for_key
                    else:
                        tower_obj["units"] = []
            
            towers.append(tower_obj)
        
        # Add the towers to the project
        combined_project["towers"] = towers
    
    # If we have unit details but no tower details, add them directly to the project
    elif unit_details_for_key and not tower_details_for_key:
        combined_project["units"] = unit_details_for_key
    
    # Format the registration number to get the ID
    if registration_number:
        formatted_id = format_id_from_registration(registration_number)
    else:
        formatted_id = key

    # Add the project to the list with id as a separate field
    all_projects.append({
        "id": formatted_id,
        **combined_project  # Spread all other properties at the same level as id
    })

# Create a backup folder if it doesn't exist

# Write the consolidated data to rera-recent.json
output_path = "final-rera-residential.json"
with open(output_path, "w") as outfile:
    json.dump(all_projects, outfile, indent=2)

print(f"Data consolidation complete! Output written to {output_path}")



print("Conversion process complete!")