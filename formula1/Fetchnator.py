# Copyright (C) 2025 eHonnef <contact@honnef.net>
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import os
import shutil

import requests
from bs4 import BeautifulSoup
import json
from dateutil import parser
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
                 fp3_dateTime, quali_dateTime, sprint_quali_dateTime, wiki_url):
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
        :param sprint_quali_dateTime: sprint qualification datetime, as defined in the iso8601
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
        self.sprint_quali_dateTime = sprint_quali_dateTime

        self.wiki_url = wiki_url

        # self.race_description = wikipedia.summary(f"{season} {race_name}")
        try:
            self.race_description = self._get_round_info()
        except requests.HTTPError:
            fetchnator_logger.error(f"Could not fetch race description from wikipedia, url={self.wiki_url}")

    def __str__(self):
        return (f"Season: {self.season}; "
                f"Round: {self.round}; "
                f"Date: {self.date}; "
                f"Race: {self.race_name}; "
                f"SprintDate: {self.sprint_dateTime}; "
                f"SprintQualiDate: {self.sprint_quali_dateTime}; "
                f"FP1Date: {self.fp1_dateTime}; "
                f"FP2Date: {self.fp2_dateTime}; "
                f"FP3Date: {self.fp3_dateTime}; "
                f"QualiDate: {self.quali_dateTime}; "
                f"\n{self.race_description}")

    def _get_round_info(self):
        fetchnator_logger.info(f"Getting data from wikipedia for round={self.round}")

        response = requests.get(self.wiki_url)
        soup = BeautifulSoup(response.text, 'html.parser')

        paragraphs = soup.find_all('p')

        return '\n'.join([para.text.strip() for para in paragraphs[:2]])

    def to_xml(self, xml_filename, mapped_dir, round_filename, title, sort_title, aired, artwork_img_ext):
        round_xml = ET.parse(f"{os.path.dirname(module_path)}/nfo-template/episode.nfo")
        round_xml.getroot().findall("./title")[0].text = title
        round_xml.getroot().findall("./sorttitle")[0].text = sort_title
        round_xml.getroot().findall("./season")[0].text = self.season
        round_xml.getroot().findall("./episode")[0].text = self.round
        round_xml.getroot().findall("./plot")[0].text = self.race_description
        round_xml.getroot().findall("./aired")[0].text = aired
        round_xml.getroot().findall("./dateadded")[0].text = date.today().isoformat()
        round_xml.getroot().findall("./year")[0].text = self.season
        round_xml.getroot().findall("./art/poster")[0].text = f"{mapped_dir}/metadata/{round_filename}{artwork_img_ext}"

        round_xml.write(xml_filename, encoding="utf-8", xml_declaration=True)

    def get_round_poster(self, filename: str, convert: str) -> None:
        """
        This is a very specific function for this specific website www.eventartworks.de.
        Replace with your own if you wish.
        :param filename: The image path that should be saved, it will be in the format season_dir_path/metadata/round_name.webp
                         Example: /data/formula 1/season 2024/metadata/Formula - 1 - s2024e19 - .Round.19.USGP.Race.webp
        :param convert: To which format should it be converted to. Check ImageConvertor class.
        """
        if convert == ImageConvertor.JPG:
            filename = os.path.splitext(filename)[0] + ".jpg"

        if os.path.exists(filename):
            fetchnator_logger.info(f"Poster already exists, no need to fetch")
            return

        round_date = datetime.strftime(parser.isoparse(self.date), "%Y-%m-%d")

        circuit_id = f"{round_date}-{self.circuit_id}"
        if f"{round_date}-{self.circuit_id}" in database.database.keys():
            circuit_id = database.database[f"{round_date}-{self.circuit_id}"]
        elif self.circuit_id in database.database.keys():
            circuit_id = f"{round_date}-{database.database[self.circuit_id]}"

        fetchnator_logger.info(
            f"Getting round poster from url=https://www.eventartworks.de/images/f1@1200/{circuit_id}.webp")
        try:
            resp = requests.get(f"https://www.eventartworks.de/images/f1@1200/{circuit_id}.webp", stream=True)
            use_default = resp.status_code != 200
        except requests.RequestException as err:
            fetchnator_logger.warning(f"Could not reach eventartworks.de for the round poster: {err}")
            use_default = True

        if not use_default:
            if resp.headers["Content-Type"] == "image/webp":
                image_bytes = resp.content
                if convert == ImageConvertor.JPG:
                    image_bytes = ImageConvertor.convert_webp_to_jpg(resp)
                with open(filename, "wb") as out_image:
                    out_image.write(image_bytes)
            else:
                use_default = True
                fetchnator_logger.warning(
                    f"Invalid url=https://www.eventartworks.de/images/f1@1200/{circuit_id}.webp\n"
                    f"Add to database: {circuit_id}")

        if use_default:
            fetchnator_logger.warning("Could not fetch round poster, using default")
            filename = os.path.splitext(filename)[0] + ".jpg"
            shutil.copy(f"{os.path.dirname(module_path)}/nfo-template/default_image.jpg", filename)


class Season:
    def __init__(self, season, start_date, end_date, season_post_url):
        self.season = season
        self.start_date = start_date
        self.end_date = end_date

        self.season_post_url = season_post_url

        self.season_info = self._get_season_info()

        self.rounds = []

    def add_round(self, round_info: RoundInfo):
        self.rounds.append(round_info)

    def get_round(self, index) -> RoundInfo | None:
        if index >= len(self.rounds):
            return None
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

        season_xml.write(filename, encoding="utf-8", xml_declaration=True)

    def get_season_poster(self, image_path) -> None:
        """
        This is a function to retrieve the season's poster from an url in self.season_post_url.
        This will be saved as .jpg.
        :param image_path: Where the image should be saved. Usually season_dir_path/folder.jpg.
                           Example: /data/formula 1/season 2024/folder.jpg
        """
        use_default = self.season_post_url is None
        if not use_default:
            response = requests.get(self.season_post_url)
            use_default = response.status_code != 200
            if not use_default:
                fetchnator_logger.info(f"Saving season={self.season} poster from {self.season_post_url}")
                with open(f"{image_path}", 'wb') as file:
                    file.write(response.content)

        if use_default:
            fetchnator_logger.warning(
                f"Could not fetch season={self.season} poster from {self.season_post_url}, using default")
            shutil.copy(f"{os.path.dirname(module_path)}/nfo-template/default_image.jpg", image_path)

    def _get_season_info(self):
        fetchnator_logger.info(f"Getting data from wikipedia for season={self.season}")
        res = requests.get(
            "https://en.wikipedia.org/w/api.php",
            params={
                "action": "query",
                "prop": "extracts",
                "exintro": True,
                "explaintext": True,
                "format": "json",
                "redirects": 1,
                "titles": f"{self.season}_Formula_One_season"
            },
            timeout=2
        )
        if res.status_code == 200:
            page_key = list(json.loads(res.content)["query"]["pages"].keys())[0]
            return json.loads(res.content)["query"]["pages"][page_key]["extract"]
        else:
            fetchnator_logger.warning(f"Could not fetch season={self.season} from wikipedia")
            # Returns a simple string.
            return f"{self.season} Formula 1 One Season"


class Fetchnator:
    def __init__(self, api="https://api.jolpi.ca/ergast/f1"):
        self.api_base = api
        # Test API connection
        requests.get(f"{self.api_base}/2011.json").raise_for_status()

        # Get season posters from thesportsdb.com
        response = requests.get("https://www.thesportsdb.com/api/v1/json/3/search_all_seasons.php?id=4370&poster=1")
        if response.status_code == 200:
            fetchnator_logger.info("Got season posters from thesportsdb.com")
            json_data = response.json()
            self.poster_data = {item["strSeason"]: item["strPoster"] for item in json_data["seasons"] if
                                item["strPoster"] is not None}

    def get_season_info(self, year: int) -> Season:
        def format_race_dict_date_time(race_dict: dict, key: str) -> str:
            rtn_str = f"{race_dict[key]['date']}"
            if "time" in race_dict[key]:
                rtn_str = f"{rtn_str}T{race_dict[key]['time']}"
            return rtn_str

        res = requests.get(
            f"{self.api_base}/{year}.json",
            timeout=10
        )
        res.raise_for_status()

        race_table = json.loads(res.content)["MRData"]["RaceTable"]
        races = race_table["Races"]
        season = Season(race_table["season"], races[0]["date"], races[-1]["date"],
                        self.poster_data.get(race_table["season"]))

        for race in races:
            obj_params = {
                "season": race["season"],
                "f1_round": race["round"],
                "round_date": f"{season.season}-01-05T00:00:00Z",  # at least put the right year.
                "race_name": race["raceName"],
                "circuit_id": race["Circuit"]["circuitId"],
                "sprint_dateTime": "",
                "fp1_dateTime": "",
                "fp2_dateTime": "",
                "fp3_dateTime": "",
                "quali_dateTime": "",
                "sprint_quali_dateTime": "",
                "wiki_url": "",
            }
            if "date" in race and "time" in race:
                obj_params["round_date"] = f"{race['date']}T{race['time']}"
            elif "date" in race:
                obj_params["round_date"] = f"{race['date']}T00:00:00Z"
            else:
                fetchnator_logger.warning(f"No date-time information for season={season.season}")

            if "url" in race:
                obj_params["wiki_url"] = race["url"]

            if "Sprint" in race:
                obj_params["sprint_dateTime"] = format_race_dict_date_time(race, "Sprint")

            if "SprintQualifying" in race:
                obj_params["sprint_quali_dateTime"] = format_race_dict_date_time(race, "SprintQualifying")
            elif "SprintShootout" in race:
                # Because why not different names, right?
                obj_params["sprint_quali_dateTime"] = format_race_dict_date_time(race, "SprintShootout")

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
