import csv
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from langex.match import generate_matches
from langex.utils import *
import argparse
import re
import json
import time
from os import listdir
from os.path import isfile


def main():
    parser = argparse.ArgumentParser(description='MSLU langex sort utility')
    parser.add_argument('-of', '--offline', action='store_true',
                        help="Do not download the files from network, open existing")
    parser.add_argument('-nofs', '--no-offline-strip', action="store_true", help="Prevent from stripping the first column of CSV\
        in offline mode")
    args = parser.parse_args()
    client = None

    log("Langex started.")

    sheets = json.load(open("./sheets_cfg.json", "r", encoding="utf-8"))

    sheets_id = json.load(open("./sheets_id.json", "r", encoding="utf-8"))
    for name in sheets_id.keys():
        if name == "__matches":
            continue
        sheets[name]["id"] = sheets_id[name]

    if not args.offline:
        scope = ['https://spreadsheets.google.com/feeds',
                 'https://www.googleapis.com/auth/drive']
        credentials = ServiceAccountCredentials.from_json_keyfile_name(
            'credentials.json', scope)

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

                log(f'Read "{filepath}"')

    if args.offline == False:
        log("Getting previous matches...", end=" ")
        table = client.open_by_key(sheets_id["__matches"]).worksheets()[0]
        tb_values = table.get_all_values()

        with open("./matches.csv", 'w', encoding="utf-8", newline="") as f:
            writer = csv.writer(f, delimiter=",")
            writer.writerows(tb_values)
        done()

    log("Generating matches...", end=" ")
    prev_matches_rows = []
    with open("matches.csv", 'r', encoding="utf-8") as f:
        for line in f.readlines()[1:]:
            line = re.sub(r"\s+;\s+", ";", line.strip())
            line = re.sub(r"\s+,\s+", ",", line)
            prev_matches_rows.append(line)

    with open("matches.csv", 'w', encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter=",")

        gen_start_time = time.time()
        matches = generate_matches(sheets)
        gen_end_time = time.time() - gen_start_time
        print("Done in", gen_end_time, "sec.")

        for match in matches:  # Merging new matches result with the old ones
            match_found = False
            for prev_match_row in prev_matches_rows:
                if prev_match_row.startswith(",".join(match[:2])):
                    writer.writerow(
                        list(match[:3]) + list(prev_match_row.split(",")[3:]))
                    match_found = True
            if not match_found:
                writer.writerow(match)

    if args.offline == False:
        log("Uploading matches...", end=" ")
        client.import_csv(sheets_id["__matches"], open(
            './matches.csv', 'r', encoding="utf-8").read())
        done()

    log("Finished.")


if __name__ == "__main__":
    main()
