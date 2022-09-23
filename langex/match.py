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
                self.user2 == obj.user2)


class Hobby:
    name = ""
    value = ""
    weight = 1.0

    def __init__(self, name, value, weight=1.0):
        self.name = name
        self.value = ",".join(sorted([i.strip() for i in value.split(",")]))

        if self.name.strip() in ["My favourite book is", "My favourite film/series is"]:
            self.weight = 0.3
        else:
            self.weight = weight

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

    def __init__(self, table_row, sheet_id):
        global column_titles

        self.sheet_id = sheet_id
        self.name = table_row[0]
        self.lng_knows = [i.strip().lower() for i in table_row[2].split(",")]
        self.lng_want_to_know = [i.strip().lower()
                                 for i in table_row[3].split(",")]
        self.hobbies = {}

        for i, cell in enumerate(table_row):
            if i in [i for i in range(6)] or i in (7, 15):
                continue

            self.hobbies[column_titles[i]] = Hobby(column_titles[i], cell)

    def __str__(self):
        return f"{self.name} #{self.sheet_id}"

    def match_with(self, user2):
        average = 0
        max_possible = 0

        for hobby_name in self.hobbies.keys():
            weight = self.hobbies[hobby_name].weight
            average += SequenceMatcher(a=self.hobbies[hobby_name].value,
                                       b=user2.hobbies[hobby_name].value).ratio()*100*weight
            max_possible += 100 * weight

        return UserMatch(self, user2, int(round(average / max_possible * 100)))


def generate_matches(sheets):
    for key in sheets.keys():

        global column_titles
        column_titles = sheets[key]["spreadsheet"][0]

        counter = 1
        for user_table_row in sheets[key]["spreadsheet"][1:]:
            users.append(User(user_table_row, f"{key}-{counter}"))
            counter += 1

    for user in users:
        for user2 in users:
            if user == user2:
                continue

            for lang in user2.lng_knows:
                if lang in user.lng_want_to_know:
                    matches.append(user.match_with(user2))

    result = [("user 1", "user 2", "match, %")]

    sorted_matches = []
    for mtch in matches:
        if not mtch in sorted_matches and mtch.percent >= 100/3:
            sorted_matches.append(mtch)

    for mtch in sorted_matches:
        result.append([mtch.user1, mtch.user2, mtch.percent])

    return result
