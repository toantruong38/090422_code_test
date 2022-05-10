import json
import constants
from columnar import columnar

users = []
organizations = []
tickets = []


def text_search(text, query):
    return query in text


def list_search(list, *elements):
    for item in list:
        if item in elements:
            return True

    return False


def read_data(location):
    try:
        f = open(location)
        data = json.load(f)

        return data
    except Exception as e:
        print("Unable to read file", e)

        return []


def print_searchable_fields():
    user_fields = "\n".join(users[0].keys())
    organization_fields = "\n".join(organizations[0].keys())
    ticket_fields = "\n".join(tickets[0].keys())

    print(
        f"Search Users with \n{user_fields}\n\nSearch Tickets with \n{ticket_fields}\n\nSearch Organizations with \n{organization_fields}\n"
    )


def prepare_data():
    global users, organizations, tickets

    users = read_data(constants.USERS_DATA_FILE_LOC)
    organizations = read_data(constants.ORGANIZATIONS_DATA_FILE_LOC)
    tickets = read_data(constants.TICKETS_DATA_FILE_LOC)


def find_user_relatives(user):
    return {
        "organization": next(
            (
                org
                for org in organizations
                if org.get("_id") == user.get("organization_id")
            ),
            {},
        ),
        "assignee_ticket": next(
            (
                ticket
                for ticket in tickets
                if ticket.get("assignee_id") == user.get("_id")
            ),
            {},
        ),
        "submitted_ticket": next(
            (
                ticket
                for ticket in tickets
                if ticket.get("submitter_id") == user.get("_id")
            ),
            {},
        ),
    }


def find_ticket_relatives(ticket):
    return {
        "organization": next(
            (
                org
                for org in organizations
                if org.get("_id") == ticket.get("organization_id")
            ),
            {},
        ),
        "assignee_user": next(
            (usr for usr in users if usr.get("_id") == ticket.get("assignee_id")),
            {},
        ),
        "submitted_user": next(
            (usr for usr in users if usr.get("_id") == ticket.get("submitter_id")),
            {},
        ),
    }


def find_organization_relatives(org):
    return {
        "ticket": next(
            (
                ticket
                for ticket in tickets
                if ticket.get("organization_id") == org.get("_id")
            )
        ),
        "users": filter(
            lambda usr: usr.get("organization_id") == org.get("_id"), users
        ),
    }


def search(table_name, field, value):
    data = []

    if table_name == "users":
        data = users
    elif table_name == "organizations":
        data = organizations
    elif table_name == "tickets":
        data = tickets
    else:
        return False

    if field not in data[0].keys():
        return False

    for rec in data:
        current_value = rec[field]
        matched = False

        if type(current_value) is list:
            matched = list_search(
                current_value, list(map(lambda v: v.strip(), value.split(",")))
            )
        else:
            matched = str(current_value) == value

        if matched:
            return rec

    return None


def print_search_option():
    option = input(
        """
    Select search options:
    - Press 1 to search
    - Press 2 to view a list of searchable fields
    """
    )

    return option


def main():
    prepare_data()

    while True:
        option = print_search_option()

        if option == "1":
            table_name_input = input(
                """
            Select 1) Users; 2) Tickets; 3) Organizations
            """
            )
            if table_name_input not in ["1", "2", "3"]:
                print("Invalid input")
                continue

            search_field = input("Enter search term\n")
            search_value = input("Enter search value\n")
            table_name = {"1": "users", "2": "tickets", "3": "organizations"}[
                table_name_input
            ]

            if table_name is None:
                print("Invalid input")
                continue

            result = search(table_name, search_field, search_value)

            if result is None:
                print("No results found")
                continue
            elif result == False:
                print("Invalid input")
                continue

            if table_name == "users":
                relative = find_user_relatives(result)

                result["assignee_ticket_subject"] = relative.get("assignee_ticket").get(
                    "subject"
                )
                result["submitted_ticket_subject"] = relative.get(
                    "submitted_ticket"
                ).get("subject")
            elif table_name == "tickets":
                relative = find_ticket_relatives(result)

                result["assignee_name"] = relative.get("assignee_user").get("name")
                result["submitter_name"] = relative.get("submitted_user").get("name")
            elif table_name == "organizations":
                relative = find_organization_relatives(result)

                result["ticket_subject"] = relative.get("ticket").get("subject")
                result["users_name"] = ", ".join(
                    map(lambda usr: usr.get("name"), relative.get("users"))
                )

            result_table = columnar(
                [list(result.values())], result.keys(), no_borders=True
            )
            print(result_table)

        elif option == "2":
            print_searchable_fields()
            continue
        else:
            return


main()
