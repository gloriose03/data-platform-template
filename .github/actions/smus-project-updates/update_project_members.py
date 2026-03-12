import os
import sys
from pathlib import Path
import yaml


checkout_env = os.environ.get("ENVIRONMENT", "").strip()
target = os.environ.get("TARGET", "").strip()
parameter_group = os.environ.get("PARAMETER_GROUP", "").strip()

print("outputs from update_project_members.py")
print(f"parameter_group: {parameter_group}")
print(f"target: {target}")
print(f"checkout_env_python: {checkout_env}")


def load_membership_file():
    """
    Looks for <parameter_group>.yaml or <parameter_group>.yml
    inside the matching parameters folder.
    """
    for dirpath in Path("parameters").iterdir():
        parts = dirpath.name.split("-")
        if len(parts) < 2:
            continue

        if parts[-1] == checkout_env and parts[-2] == target:
            print(f"Checking directory: {dirpath}")

            for entry in Path(dirpath).iterdir():
                if entry.is_dir():
                    for nested_entry in Path(entry).iterdir():
                        if nested_entry.is_file() and nested_entry.name in {
                            f"{parameter_group}.yaml",
                            f"{parameter_group}.yml",
                        }:
                            print(f"Found membership file path: {nested_entry}")
                            with open(nested_entry, "r", encoding="utf-8") as f:
                                return yaml.safe_load(f), nested_entry

    return None, None


def validate_config(config):
    if not isinstance(config, dict):
        raise ValueError("Top-level YAML structure must be a mapping/object.")

    account = config.get("account")
    members = config.get("members")

    if not isinstance(account, dict):
        raise ValueError("Missing or invalid 'account' section.")

    if not isinstance(members, list):
        raise ValueError("Missing or invalid 'members' section. It must be a list.")

    account_number = account.get("number")
    account_name = account.get("name")

    if not account_number or not account_name:
        raise ValueError("Account must include both 'number' and 'name'.")

    return account, members


def flatten_memberships(members):
    """
    Converts nested YAML into a flat list of records.
    """
    flattened = []

    for member in members:
        email = member.get("email")
        domain_projects = member.get("domain_projects", [])

        if not email:
            raise ValueError(f"Member is missing 'email': {member}")

        if not isinstance(domain_projects, list):
            raise ValueError(f"'domain_projects' must be a list for member: {email}")

        for project in domain_projects:
            domain_name = project.get("domain_name")
            project_name = project.get("project_name")
            designation = project.get("designation")

            if not domain_name or not project_name or not designation:
                raise ValueError(
                    f"Each domain_projects entry must include domain_name, "
                    f"project_name, and designation. Problem member: {email}"
                )

            flattened.append(
                {
                    "email": email.strip().lower(),
                    "domain_name": str(domain_name).strip(),
                    "project_name": str(project_name).strip(),
                    "designation": str(designation).strip(),
                }
            )

    return flattened


try:
    config, file_path = load_membership_file()

    if not config:
        print(f"CRITICAL: Could not find {parameter_group}.yaml or {parameter_group}.yml")
        sys.exit(1)

    print(f"Loaded file: {file_path}")

    account, members = validate_config(config)

    print("Account details:")
    print(f"  number: {account['number']}")
    print(f"  name  : {account['name']}")

    flattened_memberships = flatten_memberships(members)

    if not flattened_memberships:
        print("CRITICAL: No membership records found in YAML file.")
        sys.exit(1)

    print("\nProcessed membership records:")
    for idx, record in enumerate(flattened_memberships, start=1):
        print(
            f"{idx}. email={record['email']}, "
            f"domain_name={record['domain_name']}, "
            f"project_name={record['project_name']}, "
            f"designation={record['designation']}"
        )

    print(f"\nSUCCESS: Prepared {len(flattened_memberships)} membership record(s) from YAML.")
    sys.exit(0)

except Exception as e:
    print(f"CRITICAL ERROR: {str(e)}")
    sys.exit(1)
