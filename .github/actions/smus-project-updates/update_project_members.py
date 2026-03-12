import json
import os
import sys
from pathlib import Path


# Get values passed from workflow / action.yml
checkout_env = os.environ.get("ENVIRONMENT", "").strip()
parameter_group = os.environ.get("PARAMETER_GROUP", "").strip()
target = os.environ.get("TARGET", "").strip()

print("outputs from update_project_members.py")
print(f"parameter_group: {parameter_group}")
print(f"target: {target}")
print(f"checkout_env_python: {checkout_env}")

code_var = {}


def build_member_payload(member_entry):
    """
    Expected member_entry examples:
      {"type": "user", "id": "abc123"} user --> userIdentifier
      {"type": "group", "id": "group-123"} group --> groupIdentifier
    """
    member_type = str(member_entry.get("type", "")).strip().lower()
    member_id = str(member_entry.get("id", "")).strip()

    if not member_type or not member_id:
        raise ValueError(f"Invalid member entry: {member_entry}")

    if member_type == "user":
        return {"userIdentifier": member_id}

    if member_type == "group":
        return {"groupIdentifier": member_id}

    raise ValueError(f"Unsupported member type '{member_type}' in entry: {member_entry}")


# Locate and load the matching parameter file
for dirpath in Path("parameters").iterdir():
    if dirpath.name.split("-")[-1] == checkout_env and dirpath.name.split("-")[-2] == target:
        print(f"Checking directory: {dirpath}")
        for entry in Path(dirpath).iterdir():
            if entry.is_dir():
                for nested_entry in Path(entry).iterdir():
                    if nested_entry.is_file() and str(nested_entry.name) == f"{parameter_group}.json":
                        print(f"Found parameter file path: {nested_entry}")
                        with open(nested_entry, "r") as f:
                            code_var[parameter_group] = json.load(f)

if parameter_group not in code_var:
    print(f"CRITICAL: Parameter file for '{parameter_group}' was not found.")
    sys.exit(1)

print(f"Environment configs for {parameter_group}:")
for key, value in code_var[parameter_group].items():
    print(f"{key:25} : {value}")

# Expected values from JSON
DOMAIN_NAME = code_var[parameter_group].get("DOMAIN_NAME")
PROJECT_NAME = code_var[parameter_group].get("PROJECT_NAME")
MEMBERS = code_var[parameter_group].get("MEMBERS", [])
MEMBER_ACTION = str(code_var[parameter_group].get("MEMBER_ACTION", "")).strip().lower()
DESIGNATION = code_var[parameter_group].get("DESIGNATION", "PROJECT_CONTRIBUTOR")

required_vars = [DOMAIN_NAME, PROJECT_NAME, MEMBER_ACTION]

if any(v in [None, ""] for v in required_vars):
    print("CRITICAL: Missing required configuration values.")
    sys.exit(1)

if MEMBER_ACTION not in ["add", "delete"]:
    print("CRITICAL: MEMBER_ACTION must be 'add' or 'delete'.")
    sys.exit(1)

if not isinstance(MEMBERS, list):
    print("CRITICAL: MEMBERS must be a list.")
    sys.exit(1)

if not MEMBERS:
    print("CRITICAL: MEMBERS list is empty.")
    sys.exit(1)

processed_members = []

try:
    for idx, member_entry in enumerate(MEMBERS, start=1):
        member_payload = build_member_payload(member_entry)
        processed_members.append(member_payload)
        print(f"Processed member {idx}: {member_payload}")

    print("\nProcessed values ready for boto/DataZone step:")
    print(f"DOMAIN_NAME   : {DOMAIN_NAME}")
    print(f"PROJECT_NAME  : {PROJECT_NAME}")
    print(f"MEMBER_ACTION : {MEMBER_ACTION}")
    print(f"DESIGNATION   : {DESIGNATION}")
    print(f"MEMBER_COUNT  : {len(processed_members)}")
    print("MEMBER_PAYLOADS:")
    print(json.dumps(processed_members, indent=2))

    print("\nSUCCESS: Inputs validated and member payloads prepared.")
    sys.exit(0)

except Exception as e:
    print(f"CRITICAL ERROR: {str(e)}")
    sys.exit(1)
