# Copyright (C) 2024 eHonnef <contact@honnef.net>
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from Generator import Generator
import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("basefolder", help="The base folder where the Formula 1 seasons are saved.")
    parser.add_argument("-m", "--mapped-folder",
                        help="In case you are using a docker container. "
                             "Pass the docker internal path to the Formula 1 season folder. "
                             "Default will be the base folder.")

    args = parser.parse_args()
    if args.mapped_folder is None:
        args.mapped_folder = args.basefolder

    gen = Generator(args.basefolder, args.mapped_folder)
    gen.run()
