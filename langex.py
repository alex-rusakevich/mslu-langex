import csv
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from langex.match import generate_matches
from langex.utils import *


def main():
    log("Langex started.")

    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']
    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        'credentials.json', scope)

    sheets = {
        "eng": {
            "id": "1p7tMW5M9Ibedfv-FD7lw9lUC7qUd6udrPOLshnur3xk",
            "spreadsheet": []
        }
    }

    log("Logging in google services...", end=" ")
    client = gspread.authorize(credentials)
    done()

    log("Downloading tables...", end=" ")
    for lng in sheets.keys():
        sheets[lng]["spreadsheet"] = client.open_by_key(sheets[lng]["id"])
    done()

    log("Writing CSV...", end=" ")
    for lng in sheets.keys():
        spreadsheet = sheets[lng]["spreadsheet"].worksheets()[0]
        filename = lng + '-worksheet-' + \
            str(datetime.date.today()) + '.csv'
        with open(filename, 'w', encoding="utf-8", newline="") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerows(remove_column_from_matrix(
                spreadsheet.get_all_values(), 0))
    done()

    log("Generating matches...", end=" ")
    with open("matches-" + str(datetime.date.today()) + '.csv', 'w', encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerows(generate_matches(sheets))
    done()

    log("Finished.")


if __name__ == "__main__":
    main()
