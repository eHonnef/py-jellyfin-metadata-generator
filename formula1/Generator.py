# Copyright (C) 2025 eHonnef <contact@honnef.net>
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import json
import requests
import os
import re
import logging
import inspect
from Fetchnator import Fetchnator, ImageConvertor

generator_logger = logging.getLogger("Generator")
generator_module_path = inspect.getfile(inspect.currentframe())


class Generator:
    def __init__(self, base_folder: str, mapped_dir: str, convert: str) -> None:
        self.base_folder = base_folder
        self.mapped_dir = mapped_dir
        self.convert_to = convert
        try:
            generator_logger.info("Checking if API is available")
            self.fetchnator = Fetchnator()
        except requests.HTTPError:
            generator_logger.fatal("Could not fetch test data from API, exiting...")
            exit(0)
        self.config = json.load(open(f"{os.path.dirname(generator_module_path)}/config.json", "r"))

    def run(self) -> None:
        seasons = os.listdir(self.base_folder)
        generator_logger.debug(f"Seasons folders: {seasons}")
        for season_dir in seasons:
            season_dir_path = os.path.join(self.base_folder, season_dir)

            if os.path.isdir(season_dir_path):
                generator_logger.info(f"Starting to check season folder={season_dir}")

                rounds_files = os.listdir(season_dir_path)
                # generator_logger.debug(f"Round files: {rounds_files}")

                round_metadata_files = list(
                    filter(re.compile(f".*{self.config['metadata_extension']}$").match, rounds_files))
                rounds_files = list(set(rounds_files) - set(round_metadata_files))

                # Check which round file is missing its metadata
                round_with_missing_metadata = []
                for round_file in rounds_files:
                    if (not os.path.isdir(os.path.join(season_dir_path, round_file)) and
                            re.findall(rf"{self.config['season_episode_format']}", round_file, flags=re.IGNORECASE)):
                        if (f"{os.path.splitext(round_file)[0]}{self.config['metadata_extension']}"
                                not in round_metadata_files):
                            generator_logger.debug(f"Round file doesn't have metadata: {round_file}")
                            round_with_missing_metadata.append(round_file)

                if round_with_missing_metadata:
                    generator_logger.info("There is missing metadata... fetching")
                    # Check if there is the season metadata
                    contains_season_metadata = "season.nfo" in round_metadata_files

                    try:
                        # doesn't matter, just get the first one to parse the season number
                        round_file_name = round_with_missing_metadata[0]
                        parsed_season = re.findall(rf"{self.config['season_episode_format']}",
                                                   round_file_name,
                                                   flags=re.IGNORECASE)
                        if not parsed_season:
                            generator_logger.error(
                                f"Could not parse the season number from {round_with_missing_metadata[0]}. "
                                f"Please check this round file. Skipping this season={season_dir}")

                        parsed_season = parsed_season[0]
                        season_number, _ = re.findall(r"[0-9]+", parsed_season)

                        generator_logger.debug(f"Fetching full Season={season_number} info")

                        season_obj = self.fetchnator.get_season_info(season_number)

                        if not contains_season_metadata:
                            # find season artwork
                            artwork_file_name = list(filter(re.compile("folder.*").match, rounds_files))
                            if not artwork_file_name:
                                season_obj.get_season_poster(f"{season_dir_path}/folder.jpg")
                                artwork_file_name = "folder.jpg"
                            else:
                                artwork_file_name = artwork_file_name[0]

                            generator_logger.debug("Saving season to xml")
                            season_obj.to_xml(f"{season_dir_path}/season{self.config['metadata_extension']}",
                                              f"{self.mapped_dir}/{season_dir}",
                                              os.path.splitext(artwork_file_name)[1])

                    except requests.HTTPError:
                        generator_logger.error(f"Could not fetch season={season_number} from API, skipping")
                        break
                    except requests.Timeout:
                        generator_logger.error(
                            f"Could not fetch season={season_number} from API, there was a timeout, skipping")
                        break

                    # Expected format <whatever> - sXXXXeYY - <whatever>
                    for round_file_name in round_with_missing_metadata:
                        if not os.path.isdir(f"{season_dir_path}/{round_file_name}"):
                            parsed_season = re.findall(rf"{self.config['season_episode_format']}",
                                                       round_file_name,
                                                       flags=re.IGNORECASE)
                            if not parsed_season:
                                continue
                            parsed_season = parsed_season[0]
                            _, round_number = re.findall(r"[0-9]+", parsed_season)
                            generator_logger.info(f"Processing season={season_number}; round={round_number}")

                            is_sprint = re.findall(rf"{self.config['sprint']}", round_file_name, flags=re.IGNORECASE)
                            is_sprint_quali = re.findall(rf"{self.config['sprint_quali']}", round_file_name,
                                                         flags=re.IGNORECASE)
                            is_quali = re.findall(rf"{self.config['quali']}", round_file_name, flags=re.IGNORECASE)
                            is_fp1 = re.findall(rf"{self.config['fp1']}", round_file_name, flags=re.IGNORECASE)
                            is_fp2 = re.findall(rf"{self.config['fp2']}", round_file_name, flags=re.IGNORECASE)
                            is_fp3 = re.findall(rf"{self.config['fp3']}", round_file_name, flags=re.IGNORECASE)
                            is_fp = re.findall(rf"{self.config['freePractice']}", round_file_name, flags=re.IGNORECASE)

                            no_ext_round = os.path.splitext(round_file_name)[0]
                            generator_logger.debug(f"Getting round number={int(round_number)}")
                            s_round = season_obj.get_round(int(round_number) - 1)

                            if s_round is None:
                                generator_logger.warning(
                                    f"Round={int(round_number)} from Season={season_number} doesn't seem to exist. "
                                    f"Filename={round_file_name}; "
                                    f"Please check. Skipping....")
                                continue

                            round_name = s_round.race_name
                            round_sort = s_round.race_name + " 7"
                            round_date = s_round.date

                            if is_sprint:
                                generator_logger.debug("Sprint Round")
                                round_name = s_round.race_name + " - Sprint"
                                round_sort = s_round.race_name + " 6"
                                round_date = s_round.sprint_dateTime
                                # From season 2024 the sprint/sprint quali is before the quali
                                if int(season_number) >= 2024:
                                    round_sort = s_round.race_name + " 5"
                            elif is_sprint_quali:
                                generator_logger.debug("Sprint Qualification Round")
                                round_name = s_round.race_name + " - Sprint Qualification"
                                round_sort = s_round.race_name + " 5"
                                round_date = s_round.sprint_dateTime
                                # From season 2024 the sprint/sprint quali is before the quali
                                if int(season_number) >= 2024:
                                    round_sort = s_round.race_name + " 4"
                            elif is_quali:
                                generator_logger.debug("Qualification Round")
                                round_name = s_round.race_name + " - Qualification"
                                round_date = s_round.quali_dateTime
                                round_sort = s_round.race_name + " 4"
                                # From season 2024 the quali is after the sprint/sprint quali
                                if int(season_number) >= 2024:
                                    round_sort = s_round.race_name + " 6"
                            elif is_fp:
                                generator_logger.debug("Free practice round")
                                round_name = s_round.race_name + " - Free practice"
                                round_sort = s_round.race_name + " 0"
                                round_date = s_round.fp1_dateTime  # will use the first practice date and time
                            elif is_fp1:
                                generator_logger.debug("Free practice 1 round")
                                round_name = s_round.race_name + " - Free practice 1"
                                round_sort = s_round.race_name + " 1"
                                round_date = s_round.fp1_dateTime
                            elif is_fp2:
                                generator_logger.debug("Free practice 2 round")
                                round_name = s_round.race_name + " - Free practice 2"
                                round_sort = s_round.race_name + " 2"
                                round_date = s_round.fp2_dateTime
                            elif is_fp3:
                                generator_logger.debug("Free practice 3 round")
                                round_name = s_round.race_name + " - Free practice 3"
                                round_sort = s_round.race_name + " 3"
                                round_date = s_round.fp3_dateTime
                            else:
                                generator_logger.debug("No special naming in the file, considering as the race")

                            if not os.path.exists(f"{season_dir_path}/metadata"):
                                os.makedirs(f"{season_dir_path}/metadata")

                            generator_logger.debug("Getting poster")
                            try:
                                s_round.get_round_poster(f"{season_dir_path}/metadata/{no_ext_round}.webp",
                                                         self.convert_to)
                            except requests.RequestException:
                                generator_logger.error(
                                    f"Could not fetch round poster={season_dir_path}/metadata/{no_ext_round}.webp; "
                                    f"Skipping..")

                            img_extension = ".webp"
                            if self.convert_to == ImageConvertor.JPG:
                                img_extension = ".jpg"

                            generator_logger.debug("Saving round to xml")
                            s_round.to_xml(f"{season_dir_path}/{no_ext_round}{self.config['metadata_extension']}",
                                           f"{self.mapped_dir}/{season_dir}",
                                           no_ext_round,
                                           round_name,
                                           round_sort,
                                           round_date,
                                           img_extension)
                else:
                    generator_logger.info(f"No metadata missing for season={season_dir_path}")
