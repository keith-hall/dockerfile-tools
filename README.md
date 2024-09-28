# Dockerfile Tools

## Purpose

A set of tools written in Python to parse and manipulate `Dockerfile`s.
I am mainly motivated by my own use of the tools, but will happily accept contributions to cover other use-cases also :)

## Structure

### dockerfile_parser
The `dockerfile_parser` package is for super-simple parsing of "raw instruction" boundaries in a Dockerfile.
i.e. what instructions begin and end on which line.
It does no further processing. Useful for manipulating a `Dockerfile` in a later step without changing anything in the file unnecessarily for clean diffs etc.
Many other parsers etc. exist but are outdated and don't support all the changes BuildKit brought with it.
If an offical parser gets updated, we could consider swapping out this homemade parser with that one.

### instruction_parser
More user-friendly parsing of Dockerfile instructions - it takes "raw instructions" (i.e. annotated with line ranges) and parses them into more detailed instruction data classes.

### dockerfile_tools

#### get_pullable_images
Docker Desktop treats "root" images from a `Dockerfile` as cache-only, and they don't appear in a `docker image list` output.
Which means if you clear your image cache, those base images will get removed and you would have to download them again, wasting valuable time/bandwidth.
So there is a command called `get_pullable_images` which determines all the base images referenced from any stage in a given `Dockerfile`, so you can execute a `docker pull` command on them and ensure they stay when purging unused images. Or just in case you want to quickly see what images your projects are referencing at a glance.

Example usage:
```sh
poetry run python3 -- -m dockerfile_tools get_pullable_images ~/some_path_to_a/Dockerfile
```

Example output:
> public.ecr.aws/r7q2p6e2/gossm:0.3.0
> composer:2.5.5
> php:8.2.20-apache-bullseye

Further improvements planned:
- accept build arguments on the command line to resolve the images


## Developing

With a recent version of Python 3 installed and on the PATH, and Poetry package manager available, you can execute the following to get the dependencies installed:

```sh
poetry install --no-root
```

TODO: set up a Makefile or modern equivalent
TODO: set up GitHub Actions to run linters and tests
```sh
poetry run python3 -- -m ruff check
```


## Testing

```sh
poetry run python3 -- -m pytest
```
