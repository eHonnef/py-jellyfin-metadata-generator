import requests
import json
import wikipedia


class RoundInfo:
    def __init__(self, season, round_number, date, time, race_name, sprint_date=None, sprint_time=None):
        self.season = season
        self.round = round_number

        self.date = date
        self.time = time

        self.race_name = race_name
        # self.race_description = wikipedia.summary(f"{season} {race_name}")
        self.race_description = self._get_round_info()

        self.sprint_date = sprint_date
        self.sprint_time = sprint_time

    def __str__(self):
        return (f"Season: {self.season}; "
                f"Round: {self.round}; "
                f"Date: {self.date}; "
                f"Time: {self}; "
                f"Race: {self.race_name}; "
                f"SprintDate: {self.sprint_date}; "
                f"SprintTime: {self}"
                f"\n{self.race_description}")

    def _get_round_info(self):
        res = requests.get(
            f"https://en.wikipedia.org/w/api.php?action=query"
            f"&prop=extracts"
            f"&exintro"
            f"&exlimit=1"
            f"&exsectionformat=plain"
            f"&format=json"
            f"&titles={self.season} {self.race_name}"
            f"&explaintext=1"
        )
        res.raise_for_status()

        page_key = list(json.loads(res.content)["query"]["pages"].keys())[0]
        return json.loads(res.content)["query"]["pages"][page_key]["extract"]


class Season:
    def __init__(self, season, start_date, end_date):
        self.season = season
        self.start_date = start_date
        self.end_date = end_date

        self.season_info = self._get_season_info()

        self.rounds = []

    def add_round(self, round_info: RoundInfo):
        self.rounds.append(round_info)

    def _get_season_info(self):
        res = requests.get(
            f"https://en.wikipedia.org/w/api.php?action=query"
            f"&prop=extracts"
            f"&exintro"
            f"&exlimit=1"
            f"&exsectionformat=plain"
            f"&format=json"
            f"&titles={self.season}%20Formula%20One%20World%20Championship"
            f"&explaintext=1"
        )
        res.raise_for_status()

        page_key = list(json.loads(res.content)["query"]["pages"].keys())[0]
        return json.loads(res.content)["query"]["pages"][page_key]["extract"]


class Fetchnator:
    def __init__(self, api="http://ergast.com/api/f1"):
        self.api_base = api

    def get_round_info(self, year: int, round_number: int) -> RoundInfo:
        res = requests.get(
            f"{self.api_base}/{year}/{round_number}.json"
        )
        res.raise_for_status()

        race_table = json.loads(res.content)["MRData"]["RaceTable"]
        race = race_table["Races"][0]

        sprint_date_time = (None, None)
        if "Sprint" in race:
            sprint_date_time = (race["Sprint"]["date"], race["Sprint"]["time"])

        return RoundInfo(race_table["season"], race_table["round"], race["date"], race["time"], race["raceName"],
                         sprint_date_time[0], sprint_date_time[1])

    def get_season_info(self, year: int) -> Season:
        res = requests.get(
            f"{self.api_base}/{year}.json"
        )
        res.raise_for_status()

        race_table = json.loads(res.content)["MRData"]["RaceTable"]
        races = race_table["Races"]
        season = Season(race_table["season"], races[0]["date"], races[-1]["date"])

        for race in races:
            sprint_date_time = (None, None)
            if "Sprint" in race:
                sprint_date_time = (race["Sprint"]["date"], race["Sprint"]["time"])
            season.add_round(RoundInfo(race["season"], race["round"], race["date"], race["time"], race["raceName"],
                                       sprint_date_time[0], sprint_date_time[1]))

        return season
