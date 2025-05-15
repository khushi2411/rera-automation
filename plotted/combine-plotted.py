import json
import os

# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------
def load_json(filename):
    """Load a JSON file safely; return [] on failure."""
    try:
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
            print(f"✅  Loaded {filename}")
            return data
    except FileNotFoundError:
        print(f"⚠️  File {filename} not found.")
        return []
    except json.JSONDecodeError as e:
        print(f"⚠️  JSON decode error in {filename}: {e}")
        return []


def format_id_from_registration(registration_number: str) -> str:
    """
    Convert something like
    PRM/KA/RERA/1251/310/PR/030525/007705
    to
    PRM_KA_RERA_1251_310_PR_030525_007705
    """
    return registration_number.replace("/", "_") if registration_number else ""


def remove_spaces_from_keys(data):
    """
    Recursively strip spaces from *all* dict keys.
    Works for dicts and lists of arbitrary depth.
    """
    if isinstance(data, dict):
        return {k.replace(" ", ""): remove_spaces_from_keys(v) for k, v in data.items()}
    if isinstance(data, list):
        return [remove_spaces_from_keys(item) for item in data]
    return data  # primitive value – return unchanged


# ------------------------------------------------------------------
# Paths
# ------------------------------------------------------------------
base_dir = r"C:\Users\khush\scripts-rera\plotted"
project_details_path = os.path.join(base_dir, "projectdetails.json")
development_details_path = os.path.join(base_dir, "developmentdetails.json")
output_path = os.path.join(base_dir, "rera-plotted.json")

# ------------------------------------------------------------------
# Load + sanitize JSON
# ------------------------------------------------------------------
project_details_raw = load_json(project_details_path)
development_details_raw = load_json(development_details_path)

# Remove spaces in keys immediately after loading
project_details_list = remove_spaces_from_keys(project_details_raw)
development_details_list = remove_spaces_from_keys(development_details_raw)

# ------------------------------------------------------------------
# Index development details by ActionID
# ------------------------------------------------------------------
development_details_dict = {}
if isinstance(development_details_list, list):
    for item in development_details_list:
        if isinstance(item, dict) and "ActionID" in item:
            development_details_dict[item["ActionID"]] = item
elif isinstance(development_details_list, dict):
    development_details_dict = development_details_list

# ------------------------------------------------------------------
# Merge records
# ------------------------------------------------------------------
merged_projects = []

for project in project_details_list:
    if not isinstance(project, dict) or "ActionID" not in project:
        continue

    action_id = project["ActionID"]
    details_data = project.get("Details", {})

    # fetch registration # in either camelCase or spaced key
    registration_number = details_data.get("RegistrationNumber") or details_data.get(
        "Registration Number"
    )

    formatted_id = (
        format_id_from_registration(registration_number) if registration_number else action_id
    )

    # Merge development details if available
    if action_id in development_details_dict:
        dev_details = development_details_dict[action_id]

        # Standardise possible key variants
        for key in ("DevelopmentDetails", "Development Details"):
            if key in dev_details:
                details_data["DevelopmentDetails"] = dev_details[key]
                break

        if "LanduseAnalysis" in dev_details:
            details_data["LanduseAnalysis"] = dev_details["LanduseAnalysis"]

    # Final clean-up: make sure any newly-added keys are also space-free
    details_data = remove_spaces_from_keys(details_data)

    merged_projects.append(
        {
            "id": formatted_id,
            "Details": details_data,
        }
    )

# ------------------------------------------------------------------
# Output & backup
# ------------------------------------------------------------------
backup_dir = os.path.join(base_dir, "backups")
os.makedirs(backup_dir, exist_ok=True)

with open(output_path, "w", encoding="utf-8") as f:
    json.dump(merged_projects, f, ensure_ascii=False, indent=2)
print(f"✅  Consolidated data written → {output_path}")

backup_path = os.path.join(backup_dir, "plotted.json")
with open(backup_path, "w", encoding="utf-8") as f:
    json.dump(merged_projects, f, ensure_ascii=False, indent=2)
print(f"🗃️  Backup saved → {backup_path}")
