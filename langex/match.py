from langex.utils import *


class User:
    class Hobby:
        name = ""
        value = ""

    sheet_id = ""  # lang_name + user's id in a worksheet, eng-1, chn-15, etc.
    name = ""
    lng_knows = []
    lng_want_to_know = []

    hobbies = []

    def __init__(self, table_row):
        pass

    def match_percent(self, user_two):
        pass


def generate_matches(sheets):
    return []
