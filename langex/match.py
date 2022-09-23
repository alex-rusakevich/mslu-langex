from langex.utils import *
from difflib import SequenceMatcher


users = []
matches = []


class User:
    class Hobby:
        name = ""
        value = ""
        weight = 1.0

    sheet_id = ""  # lang_name + user's id in a worksheet, eng-1, chn-15, etc.
    name = ""
    lng_knows = []
    lng_want_to_know = []

    hobbies = []

    def __init__(self, table_row, sheet_id):
        self.sheet_id = sheet_id
        self.name = table_row[0]
        self.lng_knows = [i.strip().lower() for i in table_row[2].split(",")]
        self.lng_want_to_know = [i.strip().lower()
                                 for i in table_row[3].split(",")]

        table_row = [table_row[1], *table_row[4:]]
        self.hobbies = table_row


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
                self.user2 == obj.user2 and self.percent == obj.percent)


def generate_matches(sheets):
    for key in sheets.keys():
        counter = 1
        for user_table_row in sheets[key]["spreadsheet"]:
            users.append(User(user_table_row, f"{key}-{counter}"))
            counter += 1

    matches.append(UserMatch(users[0], users[1], 100))
    matches.append(UserMatch(users[1], users[0], 100))

    result = [("user 1", "user 2", "match, %")]

    sorted_matches = []
    for mtch in matches:
        if not mtch in sorted_matches and mtch.percent >= 100/3:
            sorted_matches.append(mtch)

    for mtch in sorted_matches:
        result.append([mtch.user1, mtch.user2, mtch.percent])

    return result
