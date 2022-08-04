# Version: 04.08.2022-001

import csv
import logging
from msilib.schema import Error
import os
import re
import shutil
import sys

def info(msg):
    logging.info(msg)
    print(msg)

def error(msg):
    logging.error(msg)
    print(msg)

pathToGitFolder = input("Path to abapGit repo: ")
while not os.path.isdir(pathToGitFolder + "\\src"):
    print("Entered folder doesn't exist or isn't an abapGit repository.")
    pathToGitFolder = input("Path to abapGit repo: ")
oldNamespace = input("Old namespace: ")
newNamespace = input("New namespace: ")

logging.basicConfig(level=logging.DEBUG, filename="log.txt", filemode="a+",
                    format="%(asctime)-15s %(levelname)-8s %(message)s")

info('****************************************************************************************************')

info('1) Copy files and prepare renaming...')
oldNamespace = oldNamespace.replace('/', '#').lower()
newNamespace = newNamespace.replace('/', '#').lower()

# Consider excluded files/development objects
excludedObjectsFile = None
if os.path.exists('exclude.csv'):
    excludedObjectsFile = open('exclude.csv', 'r')
    excludedObjects = excludedObjectsFile.read()
    excludedObjectsFile.close()
    excludedObjects = excludedObjects.replace('/', '#').upper()

newPathToGitFolder = pathToGitFolder + '\src_renamed'
pathToGitFolder += '\src'
shutil.copytree(pathToGitFolder, newPathToGitFolder, dirs_exist_ok=True)

info('2) Determine relevant files...')
files = []
filesToRename = []

for r, d, f in os.walk(newPathToGitFolder):
    for file in f:
        if not re.search(rf'(?i)\.bak', file) and re.search(rf'(?i)({oldNamespace}|{newNamespace})', file):
            filePath = r
            fileSegments = re.search(r'^([\w#\s]+)(\..+)$',file)
            if fileSegments is not None:
                fileName = fileSegments.group(1)
                fileExtension = fileSegments.group(2)

            newFilename = re.sub(rf'(?i){oldNamespace}', newNamespace, fileName)
            if excludedObjectsFile is None or not (re.search(rf'(?i){fileName}', excludedObjects)):
                filesToRename.append([filePath, fileName, fileExtension])
            else:
                info(rf'Exclude {fileName} and {newFilename} from renaming')
                newFilename = fileName

            files.append([filePath, newFilename, fileExtension])

info('3) Renaming files...')
for file in filesToRename:
    filePath = file[0]
    fileName = file[1]
    fileExtension = file[2]
    newFilename = ''

    if re.search(rf'(?i){oldNamespace}', fileName):
        newFilename = re.sub(rf'(?i){oldNamespace}', newNamespace, fileName)

        oldFilepath = os.path.join(filePath, fileName + fileExtension)
        newFilepath = os.path.join(filePath, newFilename + fileExtension)

        try:
            shutil.move(oldFilepath, newFilepath)
            os.remove(oldFilepath)
            file[1] = newFilename
            info(rf'{fileName}{fileExtension} => {newFilename}{fileExtension}')
        except BaseException:
            error(rf'Error: Renaming {fileName} to {newFilename} failed.')
        
    elif re.search(rf'(?i){newNamespace}', fileName):
        newFilename = fileName

info('4) Renaming occurrences within files...')
totalNumberOfExec = len(filesToRename) * len(files)
for index1, file in enumerate(filesToRename):
    # Each development object has a xml file. Some files just contain e.g. source code instead of
    # metadata of a development object. Thus no search for occurrences of these development objects
    # are necessary because the search is being done with the related xml file.
    if (re.search(rf'(?i).xml$', file[2])):
        oldObjectName = re.sub(rf'(?i){newNamespace}', oldNamespace, file[1]).replace('#', '/').upper()
        newObjectName = re.sub(rf'(?i){oldNamespace}', newNamespace, file[1]).replace('#', '/').upper()
        for index2, file2 in enumerate(files):
            filePath = os.path.join(file2[0], file2[1] + file2[2])
            print('%-50s' % oldObjectName + rf': {round(((((index1 - 1) * len(files)) + (index2 + 1)) / totalNumberOfExec) * 100, 2)}%',"\r", end=' ')
            if os.path.exists(filePath):
                with open (filePath, 'r+', encoding="utf8") as f:
                    try:
                        content = f.read()
                    except BaseException:
                        continue

                    content_new = re.sub(rf'(?i){oldObjectName}', newObjectName, content, flags = re.MULTILINE)
                    if content != content_new:
                        info(rf'>> Occurrences of {oldObjectName} replaced by {newObjectName} in {filePath}')
                        f.seek(0)
                        f.write(content_new)
                        f.truncate()

info('Executed successfully.')
input('Press any key to exit...')
