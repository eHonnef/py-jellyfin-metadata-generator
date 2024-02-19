config = {
    "base_folder": ".",
    "overwrite_nfo": False
}

import os
import re
import logging
from Fetchnator import Fetchnator

logging.basicConfig(level=logging.INFO)
generator_logger = logging.getLogger("Generator")


class Generator:
    def __init__(self, conf_file: str) -> None:
        self.base_folder = config["base_folder"]
        self.overwrite_nfo = config["overwrite_nfo"]
        self.nfo_file_regex = re.compile(".*.nfo$")
        self.fetchnator = Fetchnator()

    def run(self) -> None:
        seasons = os.listdir(self.base_folder)
        for season in seasons:
            season_folder = os.path.join(self.base_folder, season)
            if os.path.isdir(season_folder):
                episodes = os.listdir(season_folder)
                if not list(filter(lambda f: f.endswith(".nfo"), episodes)):
                    generator_logger.info(f"{season_folder} contains a .nfo file, skipping")
                    continue
                # Expected format <whatever> - sXXXXeYY - <whatever>
                for episode in episodes:
                    if not os.path.isdir(f"{season_folder}/{episode}"):
                        parsed_season = re.findall(r"s[0-9]*e[0-9]*", episode)[0]
                        season_number, episode_number = re.findall(r"[0-9]+", parsed_season)
                        generator_logger.info(f"Checking for season {season_number} episode {episode_number}")
                        res = self.fetchnator.get_round_info(season_number, episode_number)
                        # @todo: look for the season instead of the round