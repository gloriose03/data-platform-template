import boto3


def get_existing_memberships(client, domain_id, project_id):
    response = client.list_project_memberships(
        domainIdentifier=domain_id,
        projectIdentifier=project_id,
    )
    return response.get("members", [])


def add_membership(client, domain_id, project_id, user_id, designation):
    client.create_project_membership(
        domainIdentifier=domain_id,
        projectIdentifier=project_id,
        member={"userIdentifier": user_id},
        designation=designation,
    )


def remove_membership(client, domain_id, project_id, user_id):
    client.delete_project_membership(
        domainIdentifier=domain_id,
        projectIdentifier=project_id,
        member={"userIdentifier": user_id},
    )


def sync_project_memberships(grouped_memberships):
    client = boto3.client("datazone")

    for (domain_id, project_id), project_members in grouped_memberships.items():
        desired = {
            (member["email"], member["designation"])
            for member in project_members
        }

        existing_raw = get_existing_memberships(client, domain_id, project_id)

        existing = set()
        for item in existing_raw:
            member_details = item.get("memberDetails", {})
            user = member_details.get("user", {})
            user_id = user.get("userId")
            designation = item.get("designation")

            if user_id and designation:
                existing.add((user_id.lower(), designation))

        to_add = desired - existing
        to_remove = existing - desired

        for user_id, designation in sorted(to_add):
            add_membership(client, domain_id, project_id, user_id, designation)
            print(f"ADDED: {user_id} -> {domain_id}/{project_id} as {designation}")

        for user_id, designation in sorted(to_remove):
            remove_membership(client, domain_id, project_id, user_id)
            print(f"REMOVED: {user_id} from {domain_id}/{project_id} (was {designation})")
