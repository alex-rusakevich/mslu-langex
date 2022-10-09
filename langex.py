import csv
from email.errors import MisplacedEnvelopeHeaderDefect
from io import StringIO
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from langex.match import generate_matches, get_user_by_sheet_id
from langex.utils import *
import argparse
import re
import json
import time
from os import listdir
from os.path import isfile


def main():
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

    if args.send_emails:
        log("Started sending emails...", end=" ")

        def msg_gen(user_to, users_pair, match_perc):
            def join_langs(lang_list):
                if isinstance(lang_list, str):
                    return lang_list

                lgs = []
                for l in lang_list:
                    lgs.append(l.title())

                if len(lgs) == 0:
                    return ""
                elif len(lgs) == 1:
                    return lgs[0]
                else:
                    return ", ".join(lgs[:-1]) + " and " + lgs[-1]

            langs = []

            for lang in users_pair.lng_knows:
                if lang in user_to.lng_want_to_know:
                    langs.append(lang)

            for lang in user_to.lng_knows:
                if lang in users_pair.lng_want_to_know:
                    langs.append(lang)

            langs = join_langs(list(set(langs)))

            mtch = ""
            match_perc = int(match_perc)
            if match_perc > 90:
                mtch = "a perfect"
            elif match_perc > (100/3)*2:
                mtch = "an awesome"
            elif match_perc > 50:
                mtch = "a very good"
            else:
                mtch = "a"

            return f"Hello, {user_to.name}! You have {mtch} match with {users_pair.name} ({users_pair.email}), \
who speaks {join_langs(users_pair.lng_knows)}. Happy learning {langs} together!"

        sent = 0
        with open("matches.csv", 'r', encoding="utf-8") as f:
            for line in f.readlines()[1:]:
                values = list(csv.reader(
                    StringIO(line.strip()), delimiter=","))[0]

                usr1, usr2 = get_user_by_sheet_id(
                    values[0]), get_user_by_sheet_id(values[1])

                msg1_to_2 = msg_gen(usr1, usr2, values[2])
                msg2_to_1 = msg_gen(usr2, usr1, values[2])

                sent += 2

        print("Done, %i emails sent." % (sent,))

    if args.offline == False:
        log("Uploading matches...", end=" ")
        client.import_csv(sheets_id["__matches"], open(
            './matches.csv', 'r', encoding="utf-8").read())
        done()

    log("Finished.")


if __name__ == "__main__":
    main()
