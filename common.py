#!python3
#-------------------------------------------------------------------------------
# Name:        common.py
# Purpose: Assorted common functions shared between scripts.
#
# Author:      Ctrl-S
#
# Created:     04-09-2018 onwards
# Copyright:   (c) User 2018
# Licence:     <your licence>
#-------------------------------------------------------------------------------
# StdLib
import time
import os
import random
import argparse
import sys
import logging
import logging.handlers
import datetime
import re
import hashlib
##import modulefinder
# Py3-specific stdlib
import http.cookiejar as cj
# Py2-specific stdlib
##import cookielib as cj
# Remote libraries
import requests
import requests.exceptions
import psutil
# Local




CUSTOM_DELAY =1# config.delay_request# Use delay value from config file




# Constants
ONE_MEGABYTE = 1048576# 1*2^23
TEN_MEGABYTES = 102400000# 10*2^23
FIFTY_MEGABYTES = 52428800# 50*2^23
ONE_HUNDRED_MEGABYTES = 104857600# 100*2^23




def setup_logging(
    log_filepath_template='log.{ts}.txt',
    maxBytes=TEN_MEGABYTES, backupCount=10000,
    hold_filename_time=5, ):
    """Setup logging (Before running any other code)
    http://inventwithpython.com/blog/2012/04/06/stop-using-print-for-debugging-a-5-minute-quickstart-guide-to-pythons-logging-module/
    filename format:
        'myscript.log.{ts}.txt
    """
    global logger# Persist logger even if we leave current scope
    started_time = datetime.datetime.utcnow()
    timestamp = started_time.strftime("%Y-%m-%d %H.%M.%S%Z")
    # Add timetamp for filename
    # http://stackoverflow.com/questions/8472413/add-utc-time-to-filename-python
    # '2015-06-30-13.44.15'
    log_file_path = log_filepath_template.format(ts=timestamp)
    # Ensure output dir exists
    ensure_parent_dir_exists(filepath=log_file_path)
    # Instantiate global logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - f.%(filename)s - ln.%(lineno)d - %(message)s")
    # Console output
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    # File 1, log everything
    # https://docs.python.org/2/library/logging.handlers.html
    # Rollover occurs whenever the current log file is nearly maxBytes in length; if either of maxBytes or backupCount is zero, rollover never occurs.
    fh = logging.handlers.RotatingFileHandler(
        filename=log_file_path,
        # https://en.wikipedia.org/wiki/Binary_prefix
        # 104857600 100MiB
        maxBytes=maxBytes,# Above about 10MiB many text editors start to choke.
        backupCount=backupCount,
        )
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    # Place info into start of logfile
    logging.debug('log_file_path={0}'.format(log_file_path))
    logging.info('sys.argv={0}'.format(sys.argv))
    if hold_filename_time:
        time.sleep(hold_filename_time)# Make sure we can copy down the filename
    return logger



class FetchGot404(Exception):
    def __init__(self, url, response):
        self.url = url
        self.response = response
    """Pass on that there was a 404"""

def fetch(requests_session, url, method='get', data=None, expect_status=200, headers={}, minimum_resp_size=None):
    try: # Ensure we have a useragent set.
        user_agent = requests_session.headers['user-agent']
    except KeyError as k_e: # Update useragent if missing
        user_agent = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'
        if headers is None:
            headers = {'user-agent': user_agent}
        elif 'user-agent' not in headers.keys():
            headers['user-agent'] = user_agent

    for try_num in range(20): # Retry on failure.
        logging.debug('Fetch {0!r}'.format(url))
        if try_num > 1:
            backoff_time = 20*try_num
            logging.debug('Backing off for backoff_time={0!r}'.format(backoff_time))
            time.sleep(backoff_time)
        try: # Try to fetch the URL.
            if method == 'get':
                response = requests_session.get(url, headers=headers, timeout=300)
            elif method == 'post':
                response = requests_session.post(url, headers=headers, data=data, timeout=300)
            else:
                raise Exception('Unknown method')
            write_file(# Save for debug
                file_path=os.path.join('debug', 'common.fetch.last_response.html'),# Saved in this location to avoid IO operations colliding
                data=response.content
            )
            logging.debug('response.headers={0!r}'.format(response.headers))# Response headers
            logging.debug('response.request.headers={0!r}'.format(response.request.headers))# Outgoing (request) headers
        # requests exception catching
        except requests.exceptions.Timeout as err:
            logging.exception(err)
            logging.error('Caught requests.exceptions.Timeout')
            continue
        except requests.exceptions.ConnectionError as err:
            logging.exception(err)
            logging.error('Caught requests.exceptions.ConnectionError')
            continue
        except requests.exceptions.ChunkedEncodingError as err:
            logging.exception(err)
            logging.error('requests.exceptions.ChunkedEncodingError')
            continue
        # /requests exception catching
        # Allow certain error codes to be passed back out
        if response.status_code == 404:# 404 not found
            logging.error("fetch() 404 for url={0}".format(url))
            raise FetchGot404(url=url, response=response)
        if response.status_code != expect_status:
            logging.error('Problem detected. Status code mismatch. Sleeping. expect_status={es}; response.status_code={rsc}'.format(es=expect_status, rsc=response.status_code))
            write_file(# Save for debug
                file_path=os.path.join('debug', 'common.fetch.last_status_code_mismatch.html'),# Saved in this location to avoid IO operations colliding
                data=response.content
            )
            continue
        if (minimum_resp_size):# Option for response size threshold
            response_size = len(response.content)
            if  (response_size< minimum_resp_size):
                logging.error('Recieved data was too small! response_size={0}'.format(response_size))
                continue
        if CUSTOM_DELAY:
            time.sleep(CUSTOM_DELAY)
        else:
            time.sleep(random.uniform(0.5, 1.5))
        return response
    # If we can't get thing
    logging.error("fetch() giving up for url={0}".format(url))
    raise Exception('Giving up!')


def setup_requests_session(cookie_path=None, import_cookies=False):
    """Setup requests session with an optional cookiejar"""
    requests_session = requests.Session()
    # Set useragent header
    user_agent = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'
    requests_session.headers.update({'user-agent': user_agent})
    # Deal with cookie file
    ensure_parent_dir_exists(filepath=cookie_path)
    requests_session.cookies = cj.MozillaCookieJar(cookie_path)# Prepare cookiejar for later use
    if (import_cookies):
        logging.debug('Loading cookies from cookie_path={0!r}'.format(cookie_path))
        requests_session.cookies.load()
    return requests_session


def save_requests_cookies(requests_session, cookie_path):
    """Record the current cookies of the session to file"""
    logging.debug('Saving cookies to {0}'.format(cookie_path))
    ensure_parent_dir_exists(filepath=cookie_path)
    requests_session.cookies.save()
    logging.debug('Cookies saved.')
    return


# The magic two IO functions
def write_file(file_path, data):
    """Write to an file in an existing folder.
    Create dir if destination dir does not exist"""
    # Ensure output dir exists
    folder = os.path.dirname(file_path)
    if folder:
        if not os.path.exists(folder):
            os.makedirs(folder)
    assert(os.path.exists(os.path.dirname(file_path)))
    with open(file_path, 'wb') as f:
        f.write(data)
    return


def read_file(file_path):
    """Read from a file. Fail if file does not exist"""
    assert(os.path.exists(file_path))
    with open(file_path, 'rb') as f:
        data = f.read()
    return data
# /The magic two IO functions


def appendlist(lines, list_file_path, initial_text="# List of items.\n"):
    """Append a string or list of strings to a file; If no file exists, create it and append to the new file.
    Strings will be seperated by newlines. """
    # Make sure we're saving a list of strings.
    if ( type(lines) is type("") ):# Convert str to list
        lines = [lines]
    # Ensure file exists.
    ensure_parent_dir_exists(filepath=list_file_path)
    if not os.path.exists(list_file_path):
        with open(list_file_path, "w") as nf:# Initialize with header
            nf.write(initial_text)
    # Write data to file.
    with open(list_file_path, "a") as f:
        for line in lines:
            f.write('{0}\n'.format(line))
    return


def generate_filepath(root_path, filename, media_id):
    """root/type/millions/thousands/id.html"""
    padded_id_string = str(media_id).zfill(9)
    millions_section = padded_id_string[0:3]
    thousands_section = padded_id_string[3:6]
    file_path = os.path.join(
        root_path, millions_section, thousands_section, filename
        )
    return file_path


def get_hash(filename):
    # Generate hashes of script(s)
    with open(filename, 'rb') as in_file:
        return hashlib.sha1(in_file.read()).hexdigest()

def sha1(filepath):
    # Generate hashes of script(s)
    with open(filepath, 'rb') as in_file:
        return hashlib.sha1(in_file.read()).hexdigest()

def hash_file_md5(filepath):
    # Generate hasheof specified file.
    with open(filepath, 'rb') as in_file:
        return hashlib.md5(in_file.read()).hexdigest()

def ensure_parent_dir_exists(filepath):
    """Ensure output dir exists."""
    folder = os.path.dirname(filepath)
    if folder:
        if not os.path.exists(folder):
            os.makedirs(folder)
    return


def ensure_dir_exists(dir_path):
    """Ensure dir exists."""
    if dir_path:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
    return


def unixtime_ms():
    """Return the current unix time as an integer
    (milliseconds since epoch style)
    ex. 1444545370030L"""
    # https://timanovsky.wordpress.com/2009/04/09/get-unix-timestamp-in-java-python-erlang/
    current_time = time.time()
    timestamp = int(current_time *1000)
    return timestamp


def unix_time_sec():
    """Return the current unix time as an integer
    (seconds since epoch style)
    ex. 1444545553
    """
    # https://timanovsky.wordpress.com/2009/04/09/get-unix-timestamp-in-java-python-erlang/
    current_time = time.time()
    timestamp = int(current_time)
    return timestamp


##def join_dicts(x, y):
##    """Join two dicts.
##    "For dictionaries x and y, z becomes a shallowly merged dictionary with values from y replacing those from x."
##    https://stackoverflow.com/questions/38987/how-do-i-merge-two-dictionaries-in-a-single-expression
##    """
##    z = {**x, **y}
##    return z


def md5(tohash):
    """Make a md5 of a UTF8 string"""
##    logging.debug('tohash={0!r}'.format(tohash))
    hashed = hashlib.md5(tohash.encode('utf-8')).hexdigest()
##    logging.debug('hashed={0!r}'.format(hashed))
    return hashed


def range_iterator(f, low_num, high_num, *args, **kwargs):# UNTESTED
    logging.debug('range_iterator().args={0!r}'.format(locals()))# Super-debug.
    logging.info('Iterating over range from {0} through {1} (inclusive)'.format(low_num, high_num))
    for num in range(low_num, high_num+1):# low_num -> high_num inclusive
        logging.debug('Now doing {n} from range {l} -> {h}'.format(n=num, l=low_num, h=high_num))
        f(num, *args, **kwargs)
    logging.info('Done iterating over range from {0} through {1} (inclusive)'.format(low_num, high_num))



##def hash_project_files(): # TODO
##    """Record the filenames, sizes, and hashes of the files being used by the running script
##    """
##    # Figure out what modules are in use
##    modulefinder.
##    # Get their hashes
##    logging.debug('Found {n} modules in use'.format(n=len(modules)))
##    for module in modules:
##        logging.debug('module={0!r}'.format(module))
##        module_abspath = os.path.abspath(module)
##        logging.debug('module_abspath={0!r}'.format(module_abspath))
##        module_size = None
##        logging.debug('module_size={0!r}'.format(module_size))
##        module_sha1 = sha1(filepath=module)
##        logging.debug('module_sha1={0!r}'.format(module_sha1))
##        module_md5 = md5(filepath=module)
##        logging.debug('module_md5={0!r}'.format(module_md5))
##    return


def generate_list_header(filepath, data_dict, sep='\n'):
    l = [] # Lines
    l.append('# HEADER BLOCK')
    l.append('# filepath={0!r}'.format(unixtime_ms()))# Timestamp
    l.append('# unixtime_ms()={0!r}'.format(unixtime_ms()))# Timestamp
    l.append('# data_dict={0!r}'.format(data_dict))# Dump data
    l.append(sep)# Trailing sep
    output_string = sep.join(l)
    return output_string


def append_list_header(filepath, data_dict, sep='\n'):
    output_string = generate_list_header(filepath, data_dict, sep='\n')
    ensure_parent_dir_exists(filepath)
    with open(filepath, 'a') as f:
        w.write(output_string)
    return


def msleep(t, pre='sleeping for {t}', post='resuming'):
    """Sleep but with a message before and after."""
    if pre:
        print('Sleeping for {t!r}'.format(t=t))
    time.sleep(t)
    if post:
        print(post)
    return


def uniquify(seq, idfun=None):
    # List uniquifier from
    # http://www.peterbe.com/plog/uniqifiers-benchmark
   # order preserving
   if idfun is None:
       def idfun(x): return x
   seen = {}
   result = []
   for item in seq:
       marker = idfun(item)
       # in old Python versions:
       # if seen.has_key(marker)
       # but in new ones:
       if marker in seen: continue
       seen[marker] = 1
       result.append(item)
   return result


def read_listfile(filepath, silent=False):
    """Read data from a file, stripping surrounding whitespace
    and ignoring comments, and lines without text.
    If no file exists, return None.
    return a list of strings in order, where each sting is one line's text.
    """
    logging.debug('Reading filepath={0} into a list'.format(filepath))
    if not os.path.exists(filepath):
        logging.debug('File does not exist, returning None')
        return None
    # Read list file
    entries = []
    line_counter = 0
    with open(filepath, 'r') as f:
        for raw_line in f:
            line_counter += 1
            if raw_line[0] in ['#', '\n', '\r']:# Skip empty lines and comments
                continue
            if not silent:
                logging.debug('line_counter={0!r}, raw_line={1!r}'.format(line_counter, raw_line))
            cleaned_line = raw_line.strip()
            entries.append(cleaned_line)
    return entries


def read_listfile_unique(filepath):
    """Read data from a file, stripping surrounding whitespace
    and ignoring comments, and lines without text.
    If no file exists, return None.
    return a list of strings where each sting is one unique line's text. """
    logging.debug('Reading filepath={0} into a uniquified list'.format(filepath))
    lines = read_listfile(filepath)
    unique_lines = uniquify(lines)
    return unique_lines


def read_listfile_to_dict(filepath, silent=False):
    """Read data from a file, stripping surrounding whitespace
    and ignoring comments, and lines without text.
    If no file exists, return None.
    return a dict with stripped line as the key and occurances as the value."""
    logging.debug('Reading filepath={0} into a dict'.format(filepath))
    if not os.path.exists(filepath):
        logging.debug('File does not exist, returning None')
        return None
    # Read into dict
    itemsdict = {}
    line_counter = 0
    with open(filepath, 'r') as f:
        for raw_line in f:
            line_counter += 1
            if raw_line[0] in ['#', '\n', '\r']:# Skip empty lines and comments
                continue
            if not silent:
                logging.debug('line_counter={0!r}, raw_line={1!r}'.format(line_counter, raw_line))
            name = raw_line.strip()
            try:
                itemsdict[name] += 1
            except KeyError:
                itemsdict[name] = 1
    return itemsdict


def check_disk_free(bytes_req, local_path):
    """Raise an exception if there is not enough disk space"""
    # https://stackoverflow.com/questions/51658/cross-platform-space-remaining-on-volume-using-python
    # psutil.disk_usage(".").free
    bytes_free = psutil.disk_usage(local_path).free
    logging.debug('bytes_req={r!r}, bytes_free={f!r}'.format(r=bytes_req, f=bytes_free))
    if ( int(bytes_free) < int(bytes_req) ): # If not enough space make a fuss.
        logging.critical('Insufficient disk space remaining! bytes_req={r!r}, bytes_free={f!r}'.format(
            r=bytes_req, f=bytes_free))
        raise IOError('Insufficient disk space remaining! bytes_req={r!r}, bytes_free={f!r}'.format(
            r=bytes_req, f=bytes_free) )
    return # If Nothing is wrong.



def get_file_md5(filepath):
    """Get an MD5 how IA does it"""
    with open(filepath, 'rb') as f:
        return get_md5(file_object=f)


def get_md5(file_object):# https://github.com/jjjake/internetarchive/blob/1a0e5f25f9f1e924f981950fd2be7a7e5cb1f9b2/internetarchive/utils.py#L86
    m = hashlib.md5()
    while True:
        data = file_object.read(8192)
        if not data:
            break
        m.update(data)
    file_object.seek(0, os.SEEK_SET)
    return m.hexdigest()


def main():
    pass

if __name__ == '__main__':
    main()
