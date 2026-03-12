import os
import sys

from membership_config import (
    load_membership_file,
    validate_config,
    flatten_memberships,
    group_memberships_by_project,
)


def main():
    checkout_env = os.environ.get("ENVIRONMENT", "").strip()
    target = os.environ.get("TARGET", "").strip()
    parameter_group = os.environ.get("PARAMETER_GROUP", "").strip()

    print("outputs from update_project_members.py")
    print(f"parameter_group: {parameter_group}")
    print(f"target: {target}")
    print(f"checkout_env_python: {checkout_env}")

    if not checkout_env or not target or not parameter_group:
        print("CRITICAL ERROR: ENVIRONMENT, TARGET, and PARAMETER_GROUP must all be set.")
        sys.exit(1)

    try:
        config, file_path = load_membership_file(
            checkout_env=checkout_env,
            target=target,
            parameter_group=parameter_group,
        )

        print(f"Loaded file: {file_path}")

        account, members = validate_config(config)

        print("Account details:")
        print(f"  number: {account['number']}")
        print(f"  name  : {account['name']}")

        flattened_memberships = flatten_memberships(members)

        if not flattened_memberships:
            print("CRITICAL ERROR: No membership records found in YAML file.")
            sys.exit(1)

        print("\nProcessed membership records:")
        for idx, record in enumerate(flattened_memberships, start=1):
            print(
                f"{idx}. id={record['id']}, "
                f"domain_name={record['domain_name']}, "
                f"project_name={record['project_name']}, "
                f"designation={record['designation']}"
            )

        grouped_memberships = group_memberships_by_project(flattened_memberships)

        print("\nGrouped membership records by domain/project:")
        for (domain_name, project_name), project_members in grouped_memberships.items():
            print(f"- domain_name={domain_name}, project_name={project_name}")
            for member in project_members:
                print(
                    f"    id={member['id']}, designation={member['designation']}"
                )

        print(
            f"\nSUCCESS: Prepared {len(flattened_memberships)} membership record(s) from YAML."
        )
        sys.exit(0)

    except Exception as e:
        print(f"CRITICAL ERROR: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
