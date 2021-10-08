"""
Copyright (C) 2021 Red Hat, Inc. (https://github.com/Commonjava/mrrc-uploader)

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

         http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
from mrrc.utils.logs import set_logging, DEFAULT_LOGGER
from mrrc.utils.archive import detect_npm_archive, NpmArchiveType
from mrrc.pkgs.maven import handle_maven_uploading
from mrrc.config import mrrc_config
from click import command, option, argument, group, Path
import logging

logger = logging.getLogger(DEFAULT_LOGGER)


@command()
def init():
    print("init not yet implemented!")


@argument("repo", type=Path(exists=True))
@option(
    "--product",
    "-p",
    help="The product key, used to lookup profileId from the configuration",
    nargs=1,
    required=True,
)
@option(
    "--version",
    "-v",
    help="The product version, used in repository definition metadata",
    multiple=False,
)
@option(
    "--ga",
    "-g",
    is_flag=True,
    default=False,
    multiple=False,
    help="Push content to the GA group (as opposed to earlyaccess)",
)
@option("--debug", "-D", is_flag=True, default=False)
@command()
def upload(repo: str, product: str, version: str, ga=False, debug=False):
    if debug:
        set_logging(level=logging.DEBUG)
    conf = mrrc_config()
    npm_archive_type = detect_npm_archive(repo)
    product_key = f"{product}-{version}"
    if npm_archive_type != NpmArchiveType.NOT_NPM:
        # if any npm archive types....
        # Reminder: do npm repo handling here
        logger.info("This is a npm archive")
    else:
        logger.info("This is a maven archive")
        handle_maven_uploading(conf, repo, product_key, ga)


@argument("repo", type=Path(exists=True))
@option(
    "--product",
    "-p",
    help="The product key, used to lookup profileId from the configuration",
    nargs=1,
    required=True,
)
@option(
    "--version",
    "-v",
    help="The product version, used in repository definition metadata",
    multiple=False,
)
@option(
    "--ga",
    "-g",
    is_flag=True,
    default=False,
    multiple=False,
    help="Push content to the GA group (as opposed to earlyaccess)",
)
# @option('--type', '-t', is_flag=True, default="maven", multiple=False,
#               help='The package type of the product archive, default is maven')
@option("--debug", "-D", is_flag=True, default=False)
@command()
def delete(repo: str, product: str, version: str, ga=False, debug=False):
    if debug:
        set_logging(level=logging.DEBUG)
    logger.info("delete not yet implemented!")


# @option('--debug', '-D', is_flag=True, default=False)
# @command()
# def gen(debug=False):
#     if debug:
#         set_logging(level=logging.DEBUG)
#     logger.info("gen not yet implemented!")

# @option('--debug', '-D', is_flag=True, default=False)
# @command()
# def ls(debug=False):
#     if debug:
#         set_logging(level=logging.DEBUG)
#     logger.info("ls not yet implemented!")


@group()
def cli():
    pass
