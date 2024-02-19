# Formula 1 metadata generator

This will generate some metadata for your Formula 1 folder.

## Organization

For the folder structure, something like this:

```
.
└── Root(your show library, e.g.: sports)/
    └── Formula 1/
        ├── backdrop.jpg
        ├── logo.png
        ├── folder.jpg
        ├── tvshow.nfo
        ├── season 2010/
        │   ├── Formula 1 - s2010e02 - Australian Grand Prix.avi
        │   ├── <...>
        │   ├── Formula 1 - s2010e02 - Australian Grand Prix.nfo
        │   ├── <...>
        │   ├── metadata/
        │   │   ├── Formula 1 - s2010e02 - Australian Grand Prix.jpg
        │   │   └── <...>
        │   ├── folder.jpg
        │   └── season.nfo
        └── season 2023/
            ├── Formula 1 - s2023e20 - Sao Paulo Grand Prix - Race 2160p50.mp4
            ├── Formula 1 - s2023e20 - Sao Paulo Grand Prix - Sprint 2160p50.mp4
            ├── <...>
            ├── Formula 1 - s2023e20 - Sao Paulo Grand Prix - Race 2160p50.nfo
            ├── Formula 1 - s2023e20 - Sao Paulo Grand Prix - Sprint 2160p50.nfo
            ├── metadata/
            │   ├── Formula 1 - s2023e20 - Sao Paulo Grand Prix - Race 2160p50.jpg
            │   └── <...>
            ├── folder.jpg
            └── season.nfo
```

We just need to make sure that `Sprint` metadata contains a date before the `Race`.

# References

- https://www.reddit.com/r/PleX/comments/tdzp8x/formula_1_library_with_automatic_metadata/
- nfo file doc: https://jellyfin.org/docs/general/server/metadata/nfo/
- Show library doc: https://jellyfin.org/docs/general/server/media/shows
- API: http://ergast.com/mrd/
- F1 posters: https://www.eventartworks.de/index.php