import os
import shutil

import requests
import json
# import wikipedia
import inspect
import xml.etree.ElementTree as ET
from datetime import date
import logging

fetchnator_logger = logging.getLogger('Fetchnator')

module_path = inspect.getfile(inspect.currentframe())


class Database:
    def __init__(self):
        self.database = json.load(open(f"{os.path.dirname(module_path)}/circuit_alternative_name.json", "r"))


database = Database()


class RoundInfo:
    def __init__(self, season, round_number, date, time, race_name, circuit_id, sprint_date=None):
        self.season = season
        self.round = round_number
        self.circuit_id = circuit_id

        self.date = date
        self.time = time

        self.race_name = race_name
        # self.race_description = wikipedia.summary(f"{season} {race_name}")
        self.race_description = self._get_round_info()

        self.sprint_date = sprint_date

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

    def to_xml(self, xml_filename, mapped_dir, round_filename, title, aired):
        round_xml = ET.parse(f"{os.path.dirname(module_path)}/nfo-template/episode.nfo")
        round_xml.getroot().findall("./title")[0].text = title
        round_xml.getroot().findall("./season")[0].text = self.season
        round_xml.getroot().findall("./episode")[0].text = self.round
        round_xml.getroot().findall("./plot")[0].text = self.race_description
        round_xml.getroot().findall("./aired")[0].text = aired
        round_xml.getroot().findall("./dateadded")[0].text = date.today().isoformat()
        round_xml.getroot().findall("./year")[0].text = self.season
        round_xml.getroot().findall("./art/poster")[
            0].text = f"{mapped_dir}/metadata/{round_filename}.webp"

        round_xml.write(xml_filename)

    def get_round_poster(self, filename):
        circuit_id = f"{self.date}-{self.circuit_id}"
        if f"{self.date}-{self.circuit_id}" in database.database.keys():
            circuit_id = database.database[f"{self.date}-{self.circuit_id}"]
        elif self.circuit_id in database.database.keys():
            circuit_id = f"{self.date}-{database.database[self.circuit_id]}"
        fetchnator_logger.info(
            f"fetching url=https://www.eventartworks.de/images/f1@1200/{circuit_id}.webp")
        resp = requests.get(f"https://www.eventartworks.de/images/f1@1200/{circuit_id}.webp",
                            stream=True)
        resp.raise_for_status()

        if resp.headers["Content-Type"] == "image/webp":
            with open(filename, "wb") as out_image:
                shutil.copyfileobj(resp.raw, out_image)
        else:
            fetchnator_logger.warning(
                f"Invalid url=https://www.eventartworks.de/images/f1@1200/{circuit_id}.webp\n"
                f"Add to database: {circuit_id}")


class Season:
    def __init__(self, season, start_date, end_date):
        self.season = season
        self.start_date = start_date
        self.end_date = end_date

        self.season_info = self._get_season_info()

        self.rounds = []

    def add_round(self, round_info: RoundInfo):
        self.rounds.append(round_info)

    def get_round(self, index) -> RoundInfo:
        return self.rounds[index]

    def to_xml(self, filename: str, mapped_dir):
        season_xml = ET.parse(f"{os.path.dirname(module_path)}/nfo-template/season.nfo")
        season_xml.getroot().findall("./plot")[0].text = self.season_info
        season_xml.getroot().findall("./dateadded")[0].text = date.today().isoformat()
        season_xml.getroot().findall("./title")[0].text = f"Season {self.season}"
        season_xml.getroot().findall("./year")[0].text = self.season
        season_xml.getroot().findall("./premiered")[0].text = self.start_date
        season_xml.getroot().findall("./enddate")[0].text = self.end_date
        season_xml.getroot().findall("./seasonnumber")[0].text = self.season
        season_xml.getroot().findall("./art/poster")[0].text = f"{mapped_dir}/folder.jpg"

        season_xml.write(filename)

    def get_season_poster(self):
        pass

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

        sprint_date = None
        if "Sprint" in race:
            sprint_date = race["Sprint"]["date"]

        return RoundInfo(race_table["season"], race_table["round"], race["date"], race["time"], race["raceName"],
                         race["Circuit"]["circuitId"], sprint_date)

    def get_season_info(self, year: int) -> Season:
        res = requests.get(
            f"{self.api_base}/{year}.json"
        )
        res.raise_for_status()

        race_table = json.loads(res.content)["MRData"]["RaceTable"]
        races = race_table["Races"]
        season = Season(race_table["season"], races[0]["date"], races[-1]["date"])

        for race in races:
            sprint_date = None
            if "Sprint" in race:
                sprint_date = race["Sprint"]["date"]
            season.add_round(RoundInfo(race["season"], race["round"], race["date"], race["time"], race["raceName"],
                                       race["Circuit"]["circuitId"], sprint_date))

        return season
