from langex.utils import *
from difflib import SequenceMatcher


users = []
matches = []
column_titles = []


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


class Hobby:
    name = ""
    value = ""
    weight = 1.0

    def __init__(self, name, value, weight=1.0):
        self.name = name
        self.value = ",".join(sorted([i.strip() for i in value.split(",")]))
        self.weight = weight

    def __str__(self):
        return f"{self.name}({self.weight}): {self.value}"


class User:
    sheet_id = ""  # lang_name + user's id in a worksheet, eng-1, chn-15, etc.
    name = ""
    lng_knows = []
    lng_want_to_know = []

    hobbies = {}

    def __init__(self, table_row, sheet_id):
        global column_titles

        self.sheet_id = sheet_id
        self.name = table_row[0]
        self.lng_knows = [i.strip().lower() for i in table_row[2].split(",")]
        self.lng_want_to_know = [i.strip().lower()
                                 for i in table_row[3].split(",")]

        for i, cell in enumerate(table_row):
            if i in [i for i in range(4)]: 
                continue
            self.hobbies[column_titles[i]] = Hobby(column_titles[i], cell)

    def match_with(self, user2):
        average = 0
        for hobby_name in self.hobbies.keys():
            hobby = self.hobbies[hobby_name]

            average += SequenceMatcher(a=hobby.value, 
                b=user2.hobbies[hobby.name].value).ratio()*100

        return UserMatch(self, user2, int(average / len(self.hobbies)))


def generate_matches(sheets):
    for key in sheets.keys():
        
        global column_titles
        column_titles = sheets[key]["spreadsheet"][0]

        counter = 1
        for user_table_row in sheets[key]["spreadsheet"][1:]:
            users.append(User(user_table_row, f"{key}-{counter}"))
            counter += 1

    matches.append(users[0].match_with(users[1]))

    result = [("user 1", "user 2", "match, %")]

    sorted_matches = []
    for mtch in matches:
        print(mtch.percent)
        if not mtch in sorted_matches and mtch.percent >= 100/3:
            sorted_matches.append(mtch)

    for mtch in sorted_matches:
        result.append([mtch.user1, mtch.user2, mtch.percent])

    return result
