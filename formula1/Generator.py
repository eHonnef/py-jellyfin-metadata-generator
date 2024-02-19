import json

from Fetchnator import Fetchnator
import os
import re
import logging

logging.basicConfig(level=logging.WARNING)
generator_logger = logging.getLogger("Generator")


class Generator:
    def __init__(self, base_folder: str, mapped_dir: str, overwrite: bool, only_images: bool) -> None:
        self.base_folder = base_folder
        self.mapped_dir = mapped_dir
        self.overwrite_nfo = overwrite
        self.only_images = only_images
        self.fetchnator = Fetchnator()

    def run(self) -> None:
        seasons = os.listdir(self.base_folder)
        generator_logger.debug(f"Seasons folders: {seasons}")
        for season_dir in seasons:
            season_dir_path = os.path.join(self.base_folder, season_dir)

            if os.path.isdir(season_dir_path):
                generator_logger.info(f"Starting to check season folder={season_dir}")

                rounds_files = os.listdir(season_dir_path)
                generator_logger.debug(f"Round files: {rounds_files}")

                if self.only_images or not list(filter(re.compile(".*.nfo$").match, rounds_files)):
                    generator_logger.info("No .nfo files found, continuing...")
                    # Reset
                    season_obj = None
                    # Expected format <whatever> - sXXXXeYY - <whatever>
                    for round_file_name in rounds_files:
                        if not os.path.isdir(f"{season_dir_path}/{round_file_name}"):
                            parsed_season = re.findall(r"s[0-9]*e[0-9]*", round_file_name, flags=re.IGNORECASE)
                            if not parsed_season:
                                continue
                            parsed_season = parsed_season[0]
                            season_number, round_number = re.findall(r"[0-9]+", parsed_season)
                            generator_logger.info(f"Checking for season={season_number}; round={round_number}")

                            if season_obj is None:
                                generator_logger.info(f"Fething full Season={season_number} info")
                                season_obj = self.fetchnator.get_season_info(season_number)
                                season_obj.get_season_poster()
                                if not self.only_images:
                                    generator_logger.info("Saving season to xml")
                                    season_obj.to_xml(f"{season_dir_path}/season.nfo",
                                                      f"{self.mapped_dir}/{season_dir}")

                            is_sprint = re.findall(r"sprint", round_file_name, flags=re.IGNORECASE)

                            no_ext_round = os.path.splitext(round_file_name)[0]
                            generator_logger.info(f"Getting round number={int(round_number)}")
                            s_round = season_obj.get_round(int(round_number) - 1)
                            round_name = s_round.race_name
                            round_date = s_round.date
                            if is_sprint:
                                generator_logger.info("Sprint Round")
                                round_name = s_round.race_name + "- Sprint"
                                round_date = s_round.sprint_date
                            if not os.path.exists(f"{season_dir_path}/metadata"):
                                os.makedirs(f"{season_dir_path}/metadata")

                            generator_logger.info("Getting poster")
                            s_round.get_round_poster(f"{season_dir_path}/metadata/{no_ext_round}.webp")
                            if not self.only_images:
                                generator_logger.info("Saving round to xml")
                                s_round.to_xml(f"{season_dir_path}/{no_ext_round}.nfo",
                                               f"{self.mapped_dir}/{season_dir}", no_ext_round,
                                               round_name, round_date)
