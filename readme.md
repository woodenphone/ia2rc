ia2gd
InternetArchive to RClone
Utility to download from InternetArchive and upload to Rclone remotes.
Specifically targeting Google Drive, but other remotes SHOULD also work.

## Installation
### Dependancies
Psutil dependancies: (Required by code that guards against disk filling)
https://stackoverflow.com/questions/21530577/fatal-error-python-h-no-such-file-or-directory
Redhat / Centos / Fedora:
`sudo yum install -y python3-devel   # for python3.x installs`

Debian based linux (including ubuntu):
```
$ sudo apt update && sudo apt upgrade -y
$ sudo apt install -y python3 python-pip3 rclone python3-dev
```

Redhat / Centos / Fedora:
```
$ sudo yum install python3 python-pip3 rclone python3-dev
```

Required python libraries:
```
> pip3 install requests # Dependancy of "internetarchive" package, should in theory be autoinstalled by that.
> pip3 install internetarchive # Required to interact with the internet archive API
> pip3 install psutil # Used to check disk space free and guard against complete filling.
```


## Configuration
Configure Internet Archive credentials
https://archive.org/services/docs/api/internetarchive/quickstart.html
```
$ ia configure
```

Rclone must be configured with a working remote.

Only google drive remote has been tested so far, but others should work in principle.

### Google drive
https://rclone.org/drive/
This can be fiddly.

## Usage
ia2rc.py:
 Must be called from another script.
 
### Download one item by item identifier
by_identifier.py
`$python3 by_identifier.py ia_identifier local_path rc_remote_path`
ex:
`$ python3 by_identifier.py "TheAdventuresOfTomSawyer_201303" "tmp/2" "gdrive-personal:/ia2gd-test-2020/3/" --upload_every 1 --ia_file_glob_pattern "*.xml"`
`$ python3 by_identifier.py "TheAdventuresOfTomSawyer_201303" "tmp/4" "gdrive-personal:/ia2gd-test-2020/4/" --upload_every 20`

### Download multiple item by item identifier
multi_by_identifier.py:
`$ python3 multi_by_identifier.py listfile_path local_path rc_remote_path [optional args]`

Dryrun an itemlist:
`$ python3 multi_by_identifier.py "itemlist_example_1.txt" "tmp/example1" "gdrive-personal:/ia2gd-test-2020/4_example1/"  --rc_bwlimit "400K" --rc_logfile "debug/rc.log" --ia_file_glob_pattern "*.xml" --upload_every 1 --rc_dry_run --ia_dry_run `

`$ rm -rf ./memory/ # Forget all download history.`
`$ python3 multi_by_identifier.py "itemlist_example_1.txt" "tmp/example1/5" "gdrive-personal:/ia2gd-test-2020/5_example1/"  --rc_bwlimit "400K" --rc_logfile "debug/rc.log" --ia_file_glob_pattern "*.xml" --upload_every 10`

### Download all items from a specified uploader
Unimplimented.

Glob patterns (as processed by the internetarchive library) should be supplied in the form:
`"pattern1|pattern2[|pattern3...]"`

e.g. `--ia_file_glob_pattern "*.xml|*.txt|info.*"`