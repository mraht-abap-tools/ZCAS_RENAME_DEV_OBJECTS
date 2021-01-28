# ZCAS_RENAME_DEV_OBJECTS

Python script to rename multiple development objects based on an abapGit repository.

## Installation
1. Clone or copy repository
2. Install <a href="https://www.python.org/downloads/" target="_blank">Python</a> (>= 3.9.1)
3. Execute rename.py by double click (if necessary choose Python to open the file)
4. Enter path to abapGit-Repository, e.g. "D:\Downloads\ZCAS_RENAME_DEV_OBJECTS\Test-master"
5. Enter old namespace, e.g. "ZIOT_"
6. Enter new namespace, e.g. "/SCWM/"

## Exclude objects from renaming
To avoid objects to be renamed unintended add their names semicolon-separated to file 'exclude.csv'. Be aware that these files are being searched nonetheless for occurrences of objects still to be renamed.
