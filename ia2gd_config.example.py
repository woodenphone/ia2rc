#-------------------------------------------------------------------------------
# Name:        config
# Purpose:
#
# Author:      Ctrl-S
#
# Created:     05-07-2020
# Copyright:   (c) Ctrl-S 2020
# Licence:     <your licence>
#-------------------------------------------------------------------------------
import os

# InternetArchive
ia_file_glob_pattern = None
ia_dry_run = True

# Rclone
rc_bwlimit = "1M"
rc_dry_run = False
rc_logfile = os.path.join('debug', 'rclone_logfile.txt')



def main():
    pass

if __name__ == '__main__':
    main()
