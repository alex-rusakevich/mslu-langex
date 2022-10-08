from glob import glob
from langex.utils import *
from difflib import SequenceMatcher


users = []
matches = []
column_titles = []
rarely_same = []


def does_it_approx_match(a, b):
    return SequenceMatcher(a=a, b=b).ratio()*100 > 90


def get_value_by_title(row, title):
    for i, coltitle in enumerate(column_titles):
        if SequenceMatcher(a=coltitle, b=title).ratio()*100 > 93:
            return row[i]


class UserMatch:
    def __init__(self, user1, user2, percent):
        user1, user2 = sorted([user1.sheet_id, user2.sheet_id])
        self.user1 = user1
        self.user2 = user2
        self.percent = percent

    def __eq__(self, obj):
        if not isinstance(obj, UserMatch):
            return False
        return (self.user1 == obj.user1 and
                self.user2 == obj.user2)


class Hobby:
    name = ""
    value = ""
    weight = 1.0
    rarely_same = False

    def __init__(self, name, value, weight=1.0, rarely_same=False):
        self.name = name
        self.value = ",".join(sorted([i.strip() for i in value.split(",")]))
        self.rarely_same = rarely_same

    def __str__(self):
        return f"{self.name}({self.weight}): {self.value}"

    def __repr__(self):
        return self.__str__()


class User:
    sheet_id = ""  # lang_name + user's id in a worksheet, eng-1, chn-15, etc.
    name = ""
    lng_knows = []
    lng_want_to_know = []

    hobbies = {}
    email = ""

    def __init__(self, table_row, sheet_id, ignore=[], rarely_same_cols=[]):
        global column_titles
        global rarely_same
        rarely_same = rarely_same_cols

        self.sheet_id = sheet_id

        self.name = table_row[0]
        self.email = get_value_by_title(table_row, "Адрес электронной почты")

        self.lng_knows = [i.strip().lower() for i in get_value_by_title(
            table_row, "I speak...").split(",")]
        self.lng_want_to_know = [i.strip().lower()
                                 for i in get_value_by_title(table_row, "I want to learn...").split(",")]
        self.hobbies = {}

        for i, cell in enumerate(table_row):
            ignored = False
            for ign in ignore:
                if does_it_approx_match(ign, cell):
                    ignored = True
                    break

            if not ignored:
                is_rarely_same = False
                for rscol in rarely_same:

                    if does_it_approx_match(rscol, column_titles[i]):
                        is_rarely_same = True
                        break

                self.hobbies[column_titles[i]] = Hobby(
                    column_titles[i], cell.lower(), rarely_same=is_rarely_same)

    def __str__(self):
        return f"{self.name} #{self.sheet_id}"

    def match_with(self, user2):
        average = 0
        max_possible = 0

        for hobby_name in self.hobbies.keys():
            ratio = SequenceMatcher(a=self.hobbies[hobby_name].value,
                                    b=user2.hobbies[hobby_name].value).ratio()*100

            weight = 1

            if self.hobbies[hobby_name].rarely_same:

                if ratio > 80:
                    weight = 2
                else:
                    weight = 0
            else:
                weight = self.hobbies[hobby_name].weight

            average += ratio*weight
            max_possible += 100

        return UserMatch(self, user2, int(round(average / max_possible * 100)))


def generate_matches(sheets):
    for key in sheets.keys():

        global column_titles
        column_titles = sheets[key]["spreadsheet"][0]

        counter = 1
        for user_table_row in sheets[key]["spreadsheet"][1:]:
            if "".join(user_table_row).strip() == "":
                continue

            users.append(
                User(user_table_row, f"{key}-{counter}", sheets[key]["ignore"], sheets[key]["rarely_same"]))
            counter += 1

    for user in users:
        for user2 in users:
            if user == user2:
                continue

            for lang in user2.lng_knows:
                if lang in user.lng_want_to_know:
                    matches.append(user.match_with(user2))

    result = [("user#1", "user#2", "match, %", "user#1's email",
               "sent", "user#2's email", "sent")]

    sorted_matches = []
    for mtch in matches:
        if not mtch in sorted_matches and mtch.percent >= 100/3:
            sorted_matches.append(mtch)

    for mtch in sorted_matches:
        result.append([mtch.user1, mtch.user2, mtch.percent])

    return result
