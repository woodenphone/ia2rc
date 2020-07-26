#!python3
#-------------------------------------------------------------------------------
# Name:        ia2rc
# Purpose: Download items from archive.org and upload to Google Drive.
#
# Author:      Ctrl-S
#
# Created:     02-07-2020
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
import requests
# Local
import common # General-purpose functions.




def rclone_list_children(rc_remote_path:str, rc_max_depth:int, rc_logfile:str=None) -> list:
    """
    List the children of some location through rclone.
    rc_remote_path : str - rclone-style path of rclone a remote dir.
    rc_max_depth : str - rclone --max-depth numeric value.
    rc_logfile : str - rclone --log-file=foo path value.
    return a list of remote filepaths ['file1.ext', 'subdir/anotherfile.ext', 'otherdir/otherfile2.ext', 'file_no_ext',...]
    Empty dir is to be represented by an empty list.
    Return None if no data can be obtained.
    To convert output to rclone paths, prepend each child with the rclone remote path i guess.
    """
    logging.debug('rclone_upload() args={0!r}'.format(locals()))# SUPER DEBUG
    logging.info('Getting info about contents of rclone remote {0!r}'.format(rc_remote_path))
    # command - prepare args
    # https://rclone.org/commands/rclone_ls/
    cmd = [
        'rclone', 'lsjson', rc_remote_path,
        '-R',
        "--max-depth", '{0}'.format(rc_max_depth)
    ]
    if rc_logfile:# Verbose debugging info. https://rclone.org/docs/#log-level-level
        cmd.append('--log-file={0}'.format(rc_logfile))
        cmd.append('--log-level')
        cmd.append('DEBUG')
    logging.debug('cmd={0!r}'.format(cmd))
    # command - execute
    common.ensure_dir_exists(dir_path=os.path.join('debug'))# Protect against missing dir for stdout/stderr temp files.
    stdout_path = os.path.join('debug', 'ia2rc.rclone_list_children.stdout.txt')
    stderr_path = os.path.join('debug', 'ia2rc.rclone_list_children.stderr.txt')
    with open(stdout_path, 'w') as f_stdout: # File objects required to capture stdout and stderr.
        with open(stderr_path, 'w') as f_stderr:
            cmd_res = subprocess.run(
                args=cmd, encoding='utf8',
                stdout=f_stdout, stderr=f_stderr,
            )
    # command - capture and tolerate result
    logging.debug('cmd_res={0!r}'.format(cmd_res))
    if (cmd_res.returncode != 0): # Handle rclone errors.
        logging.error('Bad return code from rclone, check rc_logfile: {0}'.format(rc_logfile))
        logging.debug('cmd_res.returncode={0!r}'.format(cmd_res.returncode))
        return None # Could not get data.
    # command - interpret result
    with open(stdout_path, 'r') as res_f:# Read back from temp file
        ls_data = json.load(res_f)
    logging.debug('ls_data={0!r}'.format(ls_data)) # rclone json output for empty dir = []
    children = []
    for res in ls_data:
        children.append(res['Path'])# e.g. 'Path': 'TheAdventuresOfTomSawyer_201303/TheAdventuresOfTomSawyer_201303_meta.xml',
    logging.info('Found {c} child paths of remote path {p}'.format(c=len(children), p=rc_remote_path))
    logging.debug('children={0!r}'.format(children))
    return children



def rclone_upload(local_path:str, rc_remote_path:str, rc_bwlimit:str=None, rc_logfile:str=None, rc_dry_run:bool=False) -> None:
    """Use rclone to move something.
    https://rclone.org/docs/ """
    logging.debug('rclone_upload() args={0!r}'.format(locals()))# SUPER DEBUG
    logging.info('Using rclone to move local_path={l!r} to rc_remote_path={r!r}'.format(
        l=local_path, r=rc_remote_path))
    # command - prepare args
    # https://rclone.org/commands/rclone_move/
    cmd = [ 'rclone', 'move', local_path, rc_remote_path, ]
    if rc_bwlimit:# Throttle/ratelimit
        cmd.append('--bwlimit')
        cmd.append('{0}'.format(rc_bwlimit))
    if rc_logfile:# Verbose debugging info. https://rclone.org/docs/#log-level-level
        cmd.append('--log-file={0}'.format(rc_logfile))
        cmd.append('--log-level')
        cmd.append('DEBUG')
    if rc_dry_run: # https://rclone.org/docs/#n-dry-run
        cmd.append('--dry-run')
    logging.debug('cmd={0!r}'.format(cmd))
    # command - execute
    common.ensure_dir_exists(dir_path=os.path.join('debug'))# Protect against missing dir for stdout/stderr temp files.
    stdout_path = os.path.join('debug', 'ia2rc.rclone_upload.stdout.txt')
    stderr_path = os.path.join('debug', 'ia2rc.rclone_upload.stderr.txt')
    with open(stdout_path, 'w') as f_stdout: # File objects required to capture stdout and stderr.
        with open(stderr_path, 'w') as f_stderr:
            cmd_res = subprocess.run(
                args=cmd, encoding='utf8',
                stdout=f_stdout, stderr=f_stderr,
            )
    # command - capture and tolerate result
    logging.debug('cmd={0!r}'.format(cmd)) # Extra-detailed logging for dev only
    logging.debug('cmd_res={0!r}'.format(cmd_res))
    logging.debug('cmd_res.returncode={0!r}'.format(cmd_res.returncode))
    assert(cmd_res.returncode == 0)# Nonzero means problems occured. TODO: Check return code better -2020-07-21.
    logging.info('Finished rclone move local_path={l!r} to rc_remote_path={r!r}'.format(
        l=local_path, r=rc_remote_path))
    return


##class MaxRetriesReached(Exception):
##    """Signals that too the limit on retries has been reached"""
##def dl_ia_file_retry(identifier, filename, destdir,
##    ia_file_glob_pattern=None, ia_dry_run=False, dl_retries=10):
##    """Download a single file from an IA item.
##    Retry with exponential backoff if a failure occurs.
##    Raise an exception if retries limit is exceeded.
##    """
##    logging.debug('dl_ia_file() args={0!r}'.format(locals()))# SUPER DEBUG
##    logging.info('Attempting download for identifier={i!r} filename={f!r}'.format(
##        i=identifier, f=filename))
##    for attempt in range(1, dl_retries):
##        logging.debug('attempt={a!r} of dl_retries={m!r}'.format(a=attempt, m=dl_retries))
##        if attempt > 1:# On retry - meaning failure to download from IA
##            delay = 2 ** attempt
##            logging.info('Download failure, waiting {d} seconds'.format(d=delay))
##            time.sleep(delay) # Wait a bit because something is fucky.
##        try:
##            logging.debug('Calling IA.download()')
##            internetarchive.download(
##                identifier=identifier,
##                files=[filename],
##                destdir=destdir,
##                glob_pattern=ia_file_glob_pattern,
##                on_the_fly=False, # Do not download anything other than the origianl files.
##                verbose=True,
##                checksum=True, # skip files based on md5 checksums (safer)
##                retries = 20, # Default is 2 - https://github.com/jjjake/internetarchive/blob/master/internetarchive/files.py#L195
##                ignore_errors=False, # ignore_errors=False means pass exceptions back out of the library to the caller.
##                dry_run=ia_dry_run,
##            )
##            return # Not fatal fail
##        except requests.exceptions.ConnectionError as err:
##            logging.exception(err)
##            logging.error('ConnectionError emitted loading file from InternetArchive identifier={i!r} filename={f!r}'.format(
##                i=identifier, f=filename))
##        continue # Try again if we're allowed to.
##    # After all retries are used up, just break loudly.
##    logging.error('Too many download failures for identifier={i!r} filename={f!r}'.format(
##        i=identifier, f=filename))
##    raise MaxRetriesReached() # Give up.


class MaxRetriesReached(Exception):
    """Signals that too the limit on retries has been reached"""
def dl_ia_file_retry(file, destdir:str, dl_retries:int=100) -> None:
    """Download a single file from an IA item.
    Retry with exponential backoff if a failure occurs.
    Raise an exception if retries limit is exceeded.
    file : IA.File() instance - the file to download.
    destdir : str - path to download to.
    dl_retries : int - number of times to re-call the file.download() method before giving up.
    """
    logging.debug('dl_ia_file() args={0!r}'.format(locals()))# SUPER DEBUG
    logging.info('Attempting download for file={0!r}'.format(file))
    local_filepath = os.path.join(destdir, file.name)
    logging.debug('local_filepath={0!r}'.format(local_filepath))
    for attempt in range(1, dl_retries):
        logging.debug('attempt={a!r} of dl_retries={m!r}'.format(a=attempt, m=dl_retries))
        if attempt > 1:# On retry - meaning failure to download from IA
            delay = min(300, (2 ** (attempt-1)))# Exponential backoff up to a maximum of 5 minutes. [2,4,8,16,32,60,120,240,300,300,...] seconds.
            logging.info('Download failure, waiting {d} seconds'.format(d=delay))
            time.sleep(delay) # Wait a bit because something is fucky.
        try:
            dl_ret = file.download(
                destdir=destdir,
                verbose=True,
                checksum=True, # skip files based on md5 checksums (safer)
                retries = 100, # Default is 2 - https://github.com/jjjake/internetarchive/blob/master/internetarchive/files.py#L195
                ignore_errors=False, # ignore_errors=False means pass exceptions back out of the library to the caller.
            )
            logging.debug('dl_ret={0!r}'.format(dl_ret)) # EXPECTED to be True for success, False for fail. unsure though. This is to keep an eye on what it actually does.
            if (dl_ret is False): # Failure.
                logging.error('IA library says it failed to download {0}/{1}'.format(file.item, file.name))
                continue # Try again if we're allowed to.
            if (dl_ret is None): # No download.
                logging.info('IA library says it did not attempt a download for {0}/{1}'.format(file.item, file.name))
                return # The file is there, so success.
            if (dl_ret is True): # Success.
                if (file.format == 'Metadata'):# Special case, _files.xml hash is expected to mismatch. (Because self-hashing is very hard this file gets a hash value that does not match it)
                    logging.info('Skipping hash check for item metadata file: {0}/{1}'.format(file.item, file.name))
                else: # Normal file
                    # Verify file hash
                    local_md5 = common.get_file_md5(filepath=local_filepath)
                    logging.debug('file.md5={0!r}'.format(file.md5))
                    logging.debug('local_md5={0!r}'.format(local_md5))
                    if (local_md5 != file.md5):
                        logging.error('Hash mismatch on downloaded file: {0}'.format(local_filepath))
                        continue # Try again if permitted
                    logging.debug('Hash correct on downloaded file: {0}'.format(local_filepath))
                # After all file verification
                common.appendlist(
                    lines='{0}/{1}'.format(file.item, file.name),
                    list_file_path=os.path.join('debug', 'ia_dl_success_list.txt'),
                    initial_text='# List of successful downloads.\n# identifier/name\n'
                )
                return # Success.
        except requests.exceptions.ConnectionError as err:
            logging.exception(err)
            logging.error('ConnectionError emitted loading file from InternetArchive file={f!r}'.format(f=file))
        continue # Try again if we're allowed to.
    # After all retries are used up, just break loudly.
    logging.error('Too many download failures for file={f!r}'.format(f=file))
    raise MaxRetriesReached() # Give up.


##def dl_ia_file(identifier, filename, destdir, ## # Simple code only used once, so moved into dl_ia_item() for clarity.
##    ia_file_glob_pattern=None, ia_dry_run=False,):
##    """Download a single file from an IA item.
##    Retry with exponential backoff if a failure occurs.
##    Raise an exception if retries limit is exceeded.
##    """
##    logging.debug('dl_ia_file() args={0!r}'.format(locals()))# SUPER DEBUG
##    logging.info('Attempting download for identifier={i!r} filename={f!r}'.format(
##        i=identifier, f=filename))
##    dl_success = internetarchive.download(
##        identifier=identifier,
##        files=[filename],
##        destdir=destdir,
##        glob_pattern=ia_file_glob_pattern,
##        on_the_fly=False, # Do not download anything other than the origianl files.
##        verbose=True,
##        checksum=True, # skip files based on md5 checksums (safer)
##        retries = 20, # Default is 2 - https://github.com/jjjake/internetarchive/blob/master/internetarchive/files.py#L195
##        dry_run=ia_dry_run,
##    )
##    return dl_success



def dl_ia_item(identifier:str, local_path:str, rc_remote_path:str,
    rc_bwlimit:str=None, rc_logfile:str=None, rc_dry_run:bool=False, # RClone
    ia_file_glob_pattern:str=None, ia_dry_run:bool=False, ia_resuming:bool=True, # InternetArchive
    upload_every=1, dl_retries=100) -> None:
    """Download all original files for a given IA item
    identifier: InternetArchive unique item identifier
    upload_every upload after every n files"""
    logging.debug('dl_ia_item() args={0!r}'.format(locals()))# SUPER DEBUG
    logging.info('Attempting download for identifier={i!r}'.format(
        i=identifier))
    # Prepare paths (They are either correct or incorrect BEFORE any work is done)
    rc_remote_item_path = os.path.join(rc_remote_path, identifier) # (Assuming identifier is already a filesystem-safe slug)
    logging.debug('rc_remote_item_path={0!r}'.format(rc_remote_item_path))
    toskip_path = os.path.join('memory', 'done_files', '{0}.txt'.format(identifier) )
    common.ensure_dir_exists(dir_path=local_path) # There has to be a place to put our stuff.
    # Remember what we already did.
    to_skip = {}
    if os.path.exists(toskip_path):
        to_skip = common.read_listfile_to_dict(filepath=toskip_path, silent=True)
    logging.debug('to_skip={0!r}'.format(to_skip))
    # Get/instantiate objects for the item and its files
    item = internetarchive.get_item(identifier)
    logging.info('item={0!r}'.format(item))
    item_total_files = item.item_metadata['files_count']
    files = item.get_files(
        glob_pattern=ia_file_glob_pattern, # Ignore files based on glob preferences if any were set.
        on_the_fly=False, # Do not download anything other than the origianl files.
    )
    logging.info('files={0!r}'.format(files))
    # Download item original files
##    todo_files = len(files)# Prepare value for messages later. DOES NOT WORK - ln.99 - object of type 'generator' has no len()
    c = 0 # First item is number 1
    for file in files:
        c += 1
        logging.info('File {c} of up to {tot}'.format(c=c, tot=item_total_files))
        logging.debug('file={0!r}'.format(file))
        filename = file.name
##        logging.info('File {c} of {tot} : {fn!r}'.format(c=c, tot=item_total_files, fn=filename))
        # Handle skipping
        try: # Has this identifier+filename been done before?
            dummy = to_skip[filename]  # (classic fast existance comparison)
            logging.debug('Seen this identifier+filename before')
            if ia_resuming:
                logging.info('Skipping already downloaded file: {0!r}'.format(filename))
                continue
        except KeyError:
            pass
        # Verify download is possible
        filesize = int(file.size) # File size in bytes
        bytes_needed = filesize + common.ONE_HUNDRED_MEGABYTES
        common.check_disk_free(bytes_req=bytes_needed, local_path=local_path)
        # Perform download of this file
        logging.info('Attempting download for file={f!r}'.format(f=file))
        dl_ia_file_retry(
            file=file,
            destdir=local_path,
            dl_retries=dl_retries
        )
        # Remember we have already saved this file so partial item downloads can be resumed.
        common.appendlist(
            lines=filename,
            list_file_path=toskip_path,
            initial_text='# List of previously downloaded filenames for identifier={0!r}.\n'.format(identifier)
        )
        if upload_every and (c % upload_every == 0):
            # Perform upload via rclone
            rclone_upload(
                local_path=local_path,
                rc_remote_path=rc_remote_item_path,
                rc_bwlimit=rc_bwlimit,
                rc_logfile=rc_logfile,
                rc_dry_run=rc_dry_run
            )
    logging.debug('Finished all downloading for identifier={0}'.format(identifier))
    # Perform upload via rclone
    rclone_upload(
        local_path=local_path,
        rc_remote_path=rc_remote_item_path,
        rc_bwlimit=rc_bwlimit,
        rc_logfile=rc_logfile,
        rc_dry_run=rc_dry_run
    )
    # Remember we have already saved this item.
    common.appendlist(
        lines=identifier,
        list_file_path=os.path.join('memory', 'done_identifiers.txt',),
        initial_text='# List of previously downloaded identifiers\n',
    )
    logging.info('Finished work for identifier={i!r}'.format(i=identifier))
    return


def dl_ia_uploader(uploader:str, local_path:str, rc_remote_path:str,
    rc_bwlimit:str=None, rc_logfile:str=None, rc_dry_run:bool=False, # RClone
    ia_item_glob_pattern:str=None, ia_file_glob_pattern:str=None, ia_dry_run:bool=False, # InternetArchive
    upload_every=1, ) -> None:
    """Download all items by a given user"""
    logging.debug('dl_ia_uploader() args={0!r}'.format(locals()))# SUPER DEBUG
    logging.info('Attempting download for uploader={un!r}'.format(un=uploader))
    raise NotImplementedError()# TODO

    # Find everything by the uploader
    # Exclude by glob pattern if given
    # Process each item sequentially using its identifier
    c = 0
    n_files = len(files)
    for item in items:
        c += 1
        logging.debug('File {cur} of {tot} : {fn!r}'.format(cur=c, tot=n_files, fn=file['name']))
        dl_ia_item(
            identifier,
            local_path,
            rc_remote_path,
            ia_file_glob_pattern=None,
            upload_every=1,
            ia_dry_run=ia_dry_run,
            rc_bwlimit=rc_bwlimit,
            rc_logfile=rc_logfile,
            rc_dry_run=rc_dry_run
        )
    logging.info('Finished download for uploader={un!r}'.format(
        un=uploader))
    return


def dev() -> None:
    """Development experimentation / testing"""
    logging.info('dev() begin')
    logging.info('dev() return')
    return


def main() -> None:
    return


if __name__ == '__main__':
    logger = common.setup_logging(os.path.join("debug", "ia2rc.log.ts{ts}.txt"))# Setup logging
    try:
        main()
    except Exception as e:# Log unhandled exceptions.
        logging.critical("Unhandled exception!")
        logging.exception(e)
    logging.info('Finshed. sys.argv={0}'.format(sys.argv))
