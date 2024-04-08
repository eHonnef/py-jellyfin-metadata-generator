# Copyright (C) 2024 eHonnef <contact@honnef.net>
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import os
import requests
import json
# import wikipedia
import inspect
import xml.etree.ElementTree as ET
from datetime import date
from datetime import datetime
import logging

fetchnator_logger = logging.getLogger('Fetchnator')

module_path = inspect.getfile(inspect.currentframe())


class ImageConvertor:
    DONT = ""
    JPG = "JPG"

    @staticmethod
    def convert_webp_to_jpg(input_http_response: requests.Response) -> bytes | None:
        from PIL import Image
        from io import BytesIO

        jpg_data = None

        with BytesIO(input_http_response.content) as stream:
            im = Image.open(stream)
            jpg_stream = BytesIO()
            im.save(jpg_stream, format="jpeg")
            jpg_data = jpg_stream.getvalue()

        return jpg_data


class Database:
    def __init__(self):
        self.database = json.load(open(f"{os.path.dirname(module_path)}/circuit_alternative_name.json", "r"))


database = Database()


class RoundInfo:

    def __init__(self, season, f1_round, round_date, race_name, circuit_id, sprint_dateTime, fp1_dateTime, fp2_dateTime,
                 fp3_dateTime, quali_dateTime):
        """
        The parameters list here are the ones expected in the kwargs

        :param season: the season number
        :param f1_round: the round number
        :param round_date: date that the round happened
        :param race_name: race name
        :param circuit_id: circuit id
        :param sprint_dateTime: sprint date and time, as defined in the iso8601
        :param fp1_dateTime: fp1 date and time, as defined in the iso8601
        :param fp2_dateTime: fp2 date and time, as defined in the iso8601
        :param fp3_dateTime: fp3 date and time, as defined in the iso8601
        :param quali_dateTime: qualification datetime, as defined in the iso8601
        """
        self.season = season
        self.round = f1_round
        self.date = round_date
        self.race_name = race_name
        self.circuit_id = circuit_id
        self.sprint_dateTime = sprint_dateTime
        self.fp1_dateTime = fp1_dateTime
        self.fp2_dateTime = fp2_dateTime
        self.fp3_dateTime = fp3_dateTime
        self.quali_dateTime = quali_dateTime

        # self.race_description = wikipedia.summary(f"{season} {race_name}")
        self.race_description = self._get_round_info()

    def __str__(self):
        return (f"Season: {self.season}; "
                f"Round: {self.round}; "
                f"Date: {self.date}; "
                f"Race: {self.race_name}; "
                f"SprintDate: {self.sprint_dateTime}; "
                f"FP1Date: {self.fp1_dateTime}; "
                f"FP2Date: {self.fp2_dateTime}; "
                f"FP3Date: {self.fp3_dateTime}; "
                f"QualiDate: {self.quali_dateTime}; "
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

    def to_xml(self, xml_filename, mapped_dir, round_filename, title, aired, artwork_img_ext):
        round_xml = ET.parse(f"{os.path.dirname(module_path)}/nfo-template/episode.nfo")
        round_xml.getroot().findall("./title")[0].text = title
        round_xml.getroot().findall("./season")[0].text = self.season
        round_xml.getroot().findall("./episode")[0].text = self.round
        round_xml.getroot().findall("./plot")[0].text = self.race_description
        round_xml.getroot().findall("./aired")[0].text = aired
        round_xml.getroot().findall("./dateadded")[0].text = date.today().isoformat()
        round_xml.getroot().findall("./year")[0].text = self.season
        round_xml.getroot().findall("./art/poster")[
            0].text = f"{mapped_dir}/metadata/{round_filename}{artwork_img_ext}"

        round_xml.write(xml_filename)

    def get_round_poster(self, filename: str, convert: str):
        round_date = datetime.strftime(datetime.fromisoformat(self.date), "%Y-%m-%d")

        circuit_id = f"{round_date}-{self.circuit_id}"
        if f"{round_date}-{self.circuit_id}" in database.database.keys():
            circuit_id = database.database[f"{round_date}-{self.circuit_id}"]
        elif self.circuit_id in database.database.keys():
            circuit_id = f"{round_date}-{database.database[self.circuit_id]}"
        fetchnator_logger.info(
            f"fetching url=https://www.eventartworks.de/images/f1@1200/{circuit_id}.webp")
        resp = requests.get(f"https://www.eventartworks.de/images/f1@1200/{circuit_id}.webp",
                            stream=True)
        resp.raise_for_status()

        if resp.headers["Content-Type"] == "image/webp":
            image_bytes = resp.content
            if convert == ImageConvertor.JPG:
                filename = os.path.splitext(filename)[0] + ".jpg"
                image_bytes = ImageConvertor.convert_webp_to_jpg(resp)
            with open(filename, "wb") as out_image:
                out_image.write(image_bytes)
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

    def to_xml(self, filename: str, mapped_dir, artwork_img_ext):
        season_xml = ET.parse(f"{os.path.dirname(module_path)}/nfo-template/season.nfo")
        season_xml.getroot().findall("./plot")[0].text = self.season_info
        season_xml.getroot().findall("./dateadded")[0].text = date.today().isoformat()
        season_xml.getroot().findall("./title")[0].text = f"Season {self.season}"
        season_xml.getroot().findall("./year")[0].text = self.season
        season_xml.getroot().findall("./premiered")[0].text = self.start_date
        season_xml.getroot().findall("./enddate")[0].text = self.end_date
        season_xml.getroot().findall("./seasonnumber")[0].text = self.season
        season_xml.getroot().findall("./art/poster")[0].text = f"{mapped_dir}/folder{artwork_img_ext}"

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
        # Test API connection
        requests.get(f"{self.api_base}/2011.json").raise_for_status()

    def get_round_info(self, year: int, round_number: int) -> RoundInfo:
        # res = requests.get(
        #     f"{self.api_base}/{year}/{round_number}.json"
        # )
        # res.raise_for_status()
        #
        # race_table = json.loads(res.content)["MRData"]["RaceTable"]
        # race = race_table["Races"][0]
        #
        # sprint_date = None
        # if "Sprint" in race:
        #     sprint_date = race["Sprint"]["date"]
        #
        # return RoundInfo(race_table["season"], race_table["round"], race["date"], race["raceName"],
        #                  race["Circuit"]["circuitId"], sprint_date)
        raise NotImplemented("Not implemented")

    def get_season_info(self, year: int) -> Season:
        def format_race_dict_date_time(race_dict: dict, key: str) -> str:
            rtn_str = f"{race_dict[key]['date']}"
            if "time" in race_dict[key]:
                rtn_str = f"{rtn_str}T{race_dict[key]['time']}"
            return rtn_str

        res = requests.get(
            f"{self.api_base}/{year}.json"
        )
        res.raise_for_status()

        race_table = json.loads(res.content)["MRData"]["RaceTable"]
        races = race_table["Races"]
        season = Season(race_table["season"], races[0]["date"], races[-1]["date"])

        for race in races:
            obj_params = {
                "season": race["season"],
                "f1_round": race["round"],
                "round_date": f"{race['date']}T{race['time']}",
                "race_name": race["raceName"],
                "circuit_id": race["Circuit"]["circuitId"],
                "sprint_dateTime": "",
                "fp1_dateTime": "",
                "fp2_dateTime": "",
                "fp3_dateTime": "",
                "quali_dateTime": "",
            }
            if "Sprint" in race:
                obj_params["sprint_dateTime"] = format_race_dict_date_time(race, "Sprint")

            if "FirstPractice" in race:
                obj_params["fp1_dateTime"] = format_race_dict_date_time(race, "FirstPractice")

            if "SecondPractice" in race:
                obj_params["fp2_dateTime"] = format_race_dict_date_time(race, "SecondPractice")

            if "ThirdPractice" in race:
                obj_params["fp3_dateTime"] = format_race_dict_date_time(race, "ThirdPractice")

            if "Qualifying" in race:
                obj_params["quali_dateTime"] = format_race_dict_date_time(race, "Qualifying")

            season.add_round(RoundInfo(**obj_params))

        return season
