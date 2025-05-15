import json
import csv

def process_json_to_csv(json_file_path):
    # Read JSON data from file
    with open(json_file_path, 'r') as file:
        json_data = json.load(file)
    
    # Group items by ProjectType
    residential = [item["action_id"] for item in json_data 
                  if item["ProjectType"] == "RESIDENTIAL/GROUP HOUSING"]
    
    plotted = [item["action_id"] for item in json_data 
              if item["ProjectType"] == "PLOTTED DEVELOPMENT"]
    
    # Write to residential.csv
    with open('C:\\Users\\khush\\scripts-rera\\residential\\residential.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["ActionID"])  # Header
        for action_id in residential:
            writer.writerow([action_id])
    
    # Write to plotted.csv
    with open('C:\\Users\\khush\\scripts-rera\\plotted\\plotted.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["ActionID"])  # Header
        for action_id in plotted:
            writer.writerow([action_id])
    
    print("CSV files created successfully!")

# Use the specific file path you provided
process_json_to_csv('C:\\Users\\khush\\scripts-rera\\actionid.json')