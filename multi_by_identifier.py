#-------------------------------------------------------------------------------
# Name:        multi_by_identifier
# Purpose:
#
# Author:      Ctrl-S
#
# Created:     05-07-2020
# Copyright:   (c) Ctrl-S 2020
# Licence:     <your licence>
#-------------------------------------------------------------------------------
# StdLib
import json
import os
import sys
import logging
import re
import argparse
import time
import glob
import subprocess
# Py3-specific stdlib
# Py2-specific stdlib
# Remote libraries
import internetarchive # https://github.com/jjjake/internetarchive
import psutil
# Local
import ia2rc
import common # General-purpose functions.



def from_listfile(args):
    list_path = args.list_path
    logging.info('Processing listfile from list_path={0!r}'.format(list_path))
    with open(list_path, 'r') as f:
        line_counter = 0
        for raw_line in f:
            line_counter += 1
            if raw_line[0] in ['#', '\n', '\r']:# Skip empty lines and comments
                continue
            logging.debug('line_counter={0!r}, raw_line={1!r}'.format(line_counter, raw_line))
            cleaned_line = raw_line.strip()
            ia2rc.dl_ia_item(
                identifier=cleaned_line,
                local_path=args.local_path,
                rc_remote_path=args.rc_remote_path,
                upload_every=args.upload_every,
                ia_file_glob_pattern=args.ia_file_glob_pattern,
                ia_dry_run=args.ia_dry_run,
                rc_bwlimit=args.rc_bwlimit,
                rc_logfile=args.rc_logfile,
                rc_dry_run=args.rc_dry_run
            )
    logging.info('Finished saving items from list.')
    return


def command_line():
    # Handle command line args
    parser = argparse.ArgumentParser()
    # 'multi_by_identifier' command mandatory args
    parser.add_argument('list_path', help='filepath to a list of InternetArchive unique item identifiers',
        type=str)
    parser.add_argument('local_path', help='path to store things temporarily. (Normal format) (Used by script & fed into rclone so dont be too clever.)',
        type=str)
    parser.add_argument('rc_remote_path', help='path for rclone to push to. (Rclone format)',
        type=str)
    # 'multi_by_identifier' command optional args
    # Common optional args
    parser.add_argument('--rc_bwlimit', help='Rclone bwlimit argument, if unset will not tell rclone any bwlimit.',
        type=str, default=None)
    parser.add_argument('--rc_logfile', help='Rclone logfile argument, if unset will not tell rclone to verbosely log to a file.',
        type=str, default=None)
    parser.add_argument('--ia_file_glob_pattern', help='only download files matching this glob pattern',
        type=str, default=None)
    parser.add_argument('--upload_every', help='Upload after  every N files',
        type=int, default=None)
    parser.add_argument('--rc_dry_run', help='Only simulate rclone actions.',
        default=False, action='store_true')
    parser.add_argument('--ia_dry_run', help='Only simulate InternetArchive actions.',
        default=False, action='store_true')
    parser.set_defaults(func=from_listfile)
    args = parser.parse_args()
    logging.debug('args={args!r}'.format(args=args))# Record CLI arguments
    args.func(args)
    logging.info('Finished command-line invocation')
    return


def main():
    command_line()

if __name__ == '__main__':
    logger = common.setup_logging(os.path.join("debug", "multi_by_identifier.log.ts{ts}.txt"))# Setup logging
    try:
        main()
    except Exception as e:# Log unhandled exceptions.
        logging.critical("Unhandled exception!")
        logging.exception(e)
    logging.info('Finshed. sys.argv={0}'.format(sys.argv))