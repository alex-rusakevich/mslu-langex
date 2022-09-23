import csv
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from langex.match import generate_matches
from langex.utils import *
import argparse
import re
from os import listdir
from os.path import isfile


def main():
    parser = argparse.ArgumentParser(description='MSLU langex sort utility')
    parser.add_argument('-of', '--offline', action='store_true',
                        help="Do not download the files from network, open existing")
    parser.add_argument('-nofs', '--no-offline-strip', action="store_true", help="Prevent from stripping the first column of CSV\
        in offline mode")
    args = parser.parse_args()

    log("Langex started.")

    sheets = {}
    if not args.offline:
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
            filename = lng + '-worksheet.csv'
            with open(filename, 'w', encoding="utf-8", newline="") as f:
                writer = csv.writer(f, delimiter=";")
                writer.writerows(remove_column_from_matrix(
                    spreadsheet.get_all_values(), 0))
                sheets[lng]["spreadsheet"] = remove_column_from_matrix(
                    spreadsheet.get_all_values(), 0)
        done()
    elif args.offline == True:
        log("Offline mode on")

        file_paths = []
        for file in listdir("."):
            if not isfile(file):
                continue
            if "worksheet" in file:
                file_paths.append(file)

        for filepath in file_paths:
            with open(filepath, 'r', encoding='utf-8', newline="") as f:
                reader = csv.reader(f, delimiter=";")
                data = [row for row in reader]
                lng = re.findall(
                    r"[a-zA-Z]+(?=-)", filepath)[0].strip().lower()

                if lng == "":
                    continue

                sheets[lng] = {}
                sheets[lng]["spreadsheet"] = data

                if not args.no_offline_strip:
                    sheets[lng]["spreadsheet"] = remove_column_from_matrix(
                        sheets[lng]["spreadsheet"], 0)

                print(sheets[lng]["spreadsheet"])

                log(f'Read "{filepath}"')

    log("Generating matches...", end=" ")
    with open("matches.csv", 'w', encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerows(generate_matches(sheets))
    done()

    log("Finished.")


if __name__ == "__main__":
    main()
