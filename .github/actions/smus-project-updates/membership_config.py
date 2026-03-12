from pathlib import Path
import yaml

ALLOWED_DESIGNATIONS = {
    "PROJECT_OWNER",
    "PROJECT_CONTRIBUTOR",
    "PROJECT_CATALOG_VIEWER",
    "PROJECT_CATALOG_CONSUMER",
    "PROJECT_CATALOG_STEWARD",
}


def load_membership_file(checkout_env: str, target: str, parameter_group: str):
    """
    Looks for <parameter_group>.yaml or <parameter_group>.yml
    inside the matching parameters folder.

    Returns:
        tuple[dict, Path]: parsed YAML config and file path
    """
    parameters_path = Path("parameters")

    if not parameters_path.exists():
        raise FileNotFoundError("The 'parameters' directory does not exist.")

    for dirpath in parameters_path.iterdir():
        if not dirpath.is_dir():
            continue

        parts = dirpath.name.split("-")
        if len(parts) < 2:
            continue

        if parts[-1] == checkout_env and parts[-2] == target:
            for entry in dirpath.iterdir():
                if not entry.is_dir():
                    continue

                for nested_entry in entry.iterdir():
                    if nested_entry.is_file() and nested_entry.name in {
                        f"{parameter_group}.yaml",
                        f"{parameter_group}.yml",
                    }:
                        with open(nested_entry, "r", encoding="utf-8") as f:
                            config = yaml.safe_load(f)

                        if config is None:
                            raise ValueError(f"YAML file is empty: {nested_entry}")

                        return config, nested_entry

    raise FileNotFoundError(
        f"Could not find {parameter_group}.yaml or {parameter_group}.yml "
        f"for target='{target}' and environment='{checkout_env}'."
    )


def validate_config(config: dict):
    """
    Validates the top-level YAML structure.

    Expected shape:
    {
      "account": {
        "number": "...",
        "name": "..."
      },
      "members": [
        ...
      ]
    }

    Returns:
        tuple[dict, list]: account section, members section
    """
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


def flatten_memberships(members: list):
    """
    Converts nested YAML into a flat list of records.

    Expected member shape:
    {
      "id": "user@company.com",
      "domain_projects": [
        {
          "domain_name": "...",
          "project_name": "...",
          "designation": "PROJECT_CONTRIBUTOR"
        }
      ]
    }

    Returns:
        list[dict]
    """
    flattened = []

    for member in members:
        if not isinstance(member, dict):
            raise ValueError(f"Each member entry must be a mapping/object: {member}")

        member_id = member.get("id")
        domain_projects = member.get("domain_projects", [])

        if not member_id:
            raise ValueError(f"Member is missing 'id': {member}")

        if not isinstance(domain_projects, list):
            raise ValueError(f"'domain_projects' must be a list for member: {member_id}")

        for project in domain_projects:
            if not isinstance(project, dict):
                raise ValueError(
                    f"Each domain_projects entry must be a mapping/object. Problem member: {member_id}"
                )

            domain_name = project.get("domain_name")
            project_name = project.get("project_name")
            designation = project.get("designation")

            if not domain_name or not project_name or not designation:
                raise ValueError(
                    f"Each domain_projects entry must include domain_name, "
                    f"project_name, and designation. Problem member: {member_id}"
                )

            designation = str(designation).strip()

            if designation not in ALLOWED_DESIGNATIONS:
                raise ValueError(
                    f"Invalid designation '{designation}' for member '{member_id}'. "
                    f"Allowed values: {sorted(ALLOWED_DESIGNATIONS)}"
                )

            flattened.append(
                {
                    "id": str(member_id).strip().lower(),
                    "domain_name": str(domain_name).strip(),
                    "project_name": str(project_name).strip(),
                    "designation": designation,
                }
            )

    return flattened


def group_memberships_by_project(flattened_memberships: list):
    """
    Groups flattened memberships by (domain_name, project_name).

    Returns:
        dict[tuple[str, str], list[dict]]
    """
    grouped = {}

    for record in flattened_memberships:
        key = (record["domain_name"], record["project_name"])
        grouped.setdefault(key, []).append(
            {
                "id": record["id"],
                "designation": record["designation"],
            }
        )

    return grouped
