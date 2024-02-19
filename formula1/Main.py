from Generator import Generator
import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("basefolder", help="The base folder where the Formula 1 seasons are saved.")
    parser.add_argument("-m", "--mapped-folder",
                        help="In case you are using a docker container. Pass the docker internal path to the Formula 1 season folder. Default will be the base folder.")
    parser.add_argument("--only-images", action="store_true",
                        help="Only download the images, will not generate the metadata")
    args = parser.parse_args()
    if args.mapped_folder is None:
        args.mapped_folder = args.basefolder

    gen = Generator(args.basefolder, args.mapped_folder, False,
                    args.only_images)
    gen.run()
