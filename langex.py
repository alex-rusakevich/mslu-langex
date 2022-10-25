import csv
from email.errors import MisplacedEnvelopeHeaderDefect
from io import StringIO
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from langex.match import generate_matches, get_user_by_sheet_id
from langex.utils import *
import argparse
import re
import io
import json
import time
from os import listdir
from os.path import isfile
from langex.mail import msg_gen, send_msg, close_msg_connection


def main():
    prog_start_time = time.time()

    parser = argparse.ArgumentParser(description='MSLU langex sort utility')
    parser.add_argument('-sm', '--send-emails', action='store_true',
                        help="Send emails to all partners after generating matches")
    parser.add_argument('-of', '--offline', action='store_true',
                        help="Do not download the files from network, open existing")
    parser.add_argument('-nofs', '--no-offline-strip', action="store_true", help="Prevent from stripping the first column of CSV\
        in offline mode")
    args = parser.parse_args()
    client = None

    log("Langex started.")

    sheets = json.load(open("./sheets_cfg.json", "r", encoding="utf-8"))

    try:
        sheets_id = json.load(open("./sheets_id.json", "r", encoding="utf-8"))
    except FileNotFoundError:
        with open("./sheets_id.json", "w", encoding="utf-8") as file:
            file.writelines("""{
    "__matches": "",
    "eng": ""
}""")
            file.close()
        raise FileNotFoundError

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

    if args.send_emails:
        log("Started sending emails...")

        sent = 0
        total = 0

        new_matches_lines = []
        with open("matches.csv", 'r', encoding="utf-8") as f:
            prev_lines = f.readlines()
            new_matches_lines = []
            new_matches_lines.append(prev_lines[0])

            for line in prev_lines[1:]:
                values = list(csv.reader(
                    StringIO(line.strip()), delimiter=","))[0]

                usr1, usr2 = get_user_by_sheet_id(
                    values[0]), get_user_by_sheet_id(values[1])

                if values[4] != "Yes":
                    msg1_to_2 = msg_gen(usr1, usr2, values[2])
                    is_sent = send_msg(
                        usr1.email, "You've got a new language partner!", msg1_to_2)

                    if is_sent:
                        # Msg from 1 to 2 is sent
                        values[4] = "Yes"
                        sent += 1
                else:
                    print(
                        f"Email containing info about this partner ({usr2.email})  was already sent to {usr1.email} before.")

                if values[6] != "Yes":
                    msg2_to_1 = msg_gen(usr2, usr1, values[2])
                    is_sent = send_msg(
                        usr2.email, "You've got a new language partner!", msg2_to_1)

                    if is_sent:
                        # Msg from 2 to 1 is sent
                        values[6] = "Yes"
                        sent += 1
                else:
                    print(
                        f"Email containing info about this partner ({usr1.email}) was already sent to {usr2.email} before.")

                new_csv_line = io.StringIO()
                writer = csv.writer(new_csv_line, delimiter=",")
                writer.writerow(values)

                new_matches_lines.append(new_csv_line.getvalue())
                total += 2

        with open("matches.csv", 'w', encoding="utf-8", newline="\n") as f:
            f.writelines(new_matches_lines)

        print("Done, %i/%i emails sent." % (sent, total))
        close_msg_connection()

    if args.offline == False:
        log("Uploading matches...", end=" ")
        client.import_csv(sheets_id["__matches"], open(
            './matches.csv', 'r', encoding="utf-8").read())
        done()

    log("Finished in", time.time() - prog_start_time,"sec.")


if __name__ == "__main__":
    main()
