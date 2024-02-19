# Formula 1 metadata generator

This will generate some metadata for your Formula 1 folder.

## Expected Organization

For the round (or "episode") name, it is expected as described in
the [jellyfin documentation](https://jellyfin.org/docs/general/server/media/shows/). In short, just be sure to have
a `sXXXeYYY` name where, `XXX` is the season number and `YYY` is the round number:

```
Whatever name - s2003e12 - whatever here.
```

For the folder structure, I expect something like this:

```
.
└── Root(your show library, e.g.: sports)
    └── Formula 1
        ├── season 2010
        │   ├── Formula 1 - s2010e02 - Australian Grand Prix.avi
        │   └── ...
        └── season 2023
            ├── Formula 1 - s2023e20 - Sao Paulo Grand Prix - Race 2160p50.mp4
            ├── Formula 1 - s2023e20 - Sao Paulo Grand Prix - Sprint 2160p50.mp4
            └── ...
```

We just need to make sure that `Sprint` metadata contains a date before the `Race`.

## What will it do?

It will generate the `.nfo` files, get posters and all the good stuff... Similar to what Jellyfin automatically does by
using, e.g., the movie DB.

Your folder will become something like:

```
.
└── Root(your show library, e.g.: sports)
    └── Formula 1
        ├── backdrop.jpg
        ├── logo.png
        ├── folder.jpg
        ├── tvshow.nfo
        ├── season 2010
        │   ├── Formula 1 - s2010e02 - Australian Grand Prix.avi
        │   ├── <...>
        │   ├── Formula 1 - s2010e02 - Australian Grand Prix.nfo
        │   ├── <...>
        │   ├── metadata
        │   │   ├── Formula 1 - s2010e02 - Australian Grand Prix.jpg
        │   │   └── <...>
        │   ├── folder.jpg
        │   └── season.nfo
        └── season 2023
            ├── Formula 1 - s2023e20 - Sao Paulo Grand Prix - Race 2160p50.mp4
            ├── Formula 1 - s2023e20 - Sao Paulo Grand Prix - Sprint 2160p50.mp4
            ├── <...>
            ├── Formula 1 - s2023e20 - Sao Paulo Grand Prix - Race 2160p50.nfo
            ├── Formula 1 - s2023e20 - Sao Paulo Grand Prix - Sprint 2160p50.nfo
            ├── metadata
            │   ├── Formula 1 - s2023e20 - Sao Paulo Grand Prix - Race 2160p50.jpg
            │   └── <...>
            ├── folder.jpg
            └── season.nfo
```

**Some important notes**:

- If there is already a `.nfo` file inside the season folder, then it will be skipped. Unless you set the
  option `--rewrite`.

## How does it work?

- It will fetch the data from [ergast](http://ergast.com/mrd/). I wrote a small wrapper because they said that the
  service will be discontinued by the end of 2024 :(
- It will download the race posters from [Event Artworks](https://www.eventartworks.de)
- The race and season description is taken from Wikipedia.

## How do I use it?

- Check the help section: `python3 Main.py -h`
- Example: `python3 Main.py /path/to/my/f1/library`
- Are you using a docker container for Jellyfin? Then: `python3 Main.py /path/to/my/f1/library --mapped-folder /media/shows/f1`
- Do you only want the posters? Then: `python3 Main.py /path/to/my/f1/library --mapped-folder /media/shows/f1 --only-images`

## Requirements

- Nothing besides the standard python lib
- Tested with python 12+. Maybe it will run on older versions.

## Roadmap

- Add a decent Wikipedia API request.
- Add support for different languages from Wikipedia.
- Add error handling

# References

- https://www.reddit.com/r/PleX/comments/tdzp8x/formula_1_library_with_automatic_metadata/
- nfo file doc: https://jellyfin.org/docs/general/server/metadata/nfo/
- Show library doc: https://jellyfin.org/docs/general/server/media/shows
- API: http://ergast.com/mrd/
- F1 posters: https://www.eventartworks.de/index.php
