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

or to pull immediately add this to the end of the invocation above:
```sh
| xargs -n 1 -- docker pull
```

Further improvements planned:
- accept build arguments on the command line to resolve the images

https://docs.docker.com/reference/dockerfile/#predefined-args

### inject_proxy_ca
If you find yourself wanting to use Docker behind a proxy server, for example to cache packages in the case of slow/limited internet connectivity, then you will likely need the Dockerfile to be modified to accept the CA certificate, and perhaps to direct certain commands through the proxy. This tool will automate it for you.
This is currently done with a simple regex search on the executable name - TODO: perhaps it would be possible to use a proper Bash parser for better behavior?
If you are wondering why not just set the `HTTPS_PROXY` build arg, well, the Dockerfile has to change anyway for the CA cert. And it could be invoked by docker compose, in which case the compose file has to change. Or, in many cases `Makefile` recipies are used, and those would also have to change. It seemed simpler to just modify the one file, and only where it makes sense to go via the proxy for caching purposes.
TODO: Ideally it would also be more configurable about which calls to add the proxy env var to
TODO: allow in place edits from the CLI (but warn if not part of a git repo or if the Dockerfile is untracked or already modified etc.)
TODO: perhaps use a rules file instead of hardcoded
TODO: support undoing changes? Or relying on git is good enough?

Example usage:
```sh
http_proxy='http://host.docker.internal:3128' poetry run python3 -- -m dockerfile_tools inject_proxy_ca ~/some_path_to_a/Dockerfile ~/.config/proxy-kutti/rootCA.pem > new_dockerfile
```

If you encounter problems with `apt` and GPG invalid signatures, for example because you used `docker compose build --build-arg HTTPS_PROXY=http://host.docker.internal:3128` without having run this CA cert injection first, it should be safe to do:
`docker builder prune --all` and try again.

## Developing

With a recent version of Python 3 installed and on the PATH, and Poetry package manager available, you can execute the following to get the dependencies installed:

```sh
poetry install --no-root
```

### Python setup

To get Python 3 setup on Linux (without getting the dreaded libssl v1.0 problems), for example you could do something like this:
```sh
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt-get install python3.12-full

python3.12 -m venv ./.venv
source .venv/bin/activate
pip install poetry
```
followed by the
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
