import csv
import logging
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

pathToGitFolder = input("Path to abapGit repo: ") + "\\src"
while not os.path.isdir(pathToGitFolder):
    print("Entered folder doesn't exist or isn't an abapGit repository.")
    pathToGitFolder = input("Path to abapGit repo: ") + "\\src"
oldNamespace = input("Old namespace: ")
newNamespace = input("New namespace: ")

logging.basicConfig(level=logging.DEBUG, filename="log.txt", filemode="a+",
                    format="%(asctime)-15s %(levelname)-8s %(message)s")

info('****************************************************************************************************')

# Consider excluded files/development objects
excludedObjectsFile = open('exclude.csv', 'r')
excludedObjects = excludedObjectsFile.read()
excludedObjectsFile.close()
excludedObjects = excludedObjects.replace('/', '#').upper()

oldNamespace = oldNamespace.replace('/', '#').lower()
newNamespace = newNamespace.replace('/', '#').lower()

info('1) Determine relevant files...')
files = []
filesToRename = []

for r, d, f in os.walk(pathToGitFolder):
    for file in f:
        if not re.search(rf'(?i)\.bak', file) and re.search(rf'(?i)({oldNamespace}|{newNamespace})', file):
            filePath = r
            fileSegments = re.search(r'^([\w#]+)(\..+)$',file)
            fileName = fileSegments.group(1)
            fileExtension = fileSegments.group(2)

            newFilename = re.sub(rf'(?i){oldNamespace}', newNamespace, fileName)
            if not (re.search(rf'(?i){fileName}', excludedObjects)):
                filesToRename.append([filePath, fileName, fileExtension])
            else:
                info(rf'Exclude {fileName} and {newFilename} from renaming')
                newFilename = fileName

            files.append([filePath, newFilename, fileExtension])

info('2) Renaming files...')
for file in filesToRename:
    filePath = file[0]
    fileName = file[1]
    fileExtension = file[2]
    newFilename = ''

    if re.search(rf'(?i){oldNamespace}', fileName):
        newFilename = re.sub(rf'(?i){oldNamespace}', newNamespace, fileName)

        oldFilepath = os.path.join(filePath, fileName + fileExtension)
        newFilepath = os.path.join(filePath, newFilename + fileExtension)
        if shutil.move(oldFilepath, newFilepath):
            file[1] = newFilename
            info(rf'{fileName} => {newFilename}')
        else:
            error(rf'Error: Renaming {fileName} to {newFilename} failed.')
        
    elif re.search(rf'(?i){newNamespace}', fileName):
        newFilename = fileName

info('3) Renaming occurrences within files...')
for file in filesToRename:
    # Each development object has a xml file. Some files just contain e.g. source code instead of
    # metadata of a development object. Thus no search for occurrences of these development objects
    # are necessary because the search is being done with the related xml file.
    if (re.search(rf'(?i).xml$', file[2])):
        oldObjectName = re.sub(rf'(?i){newNamespace}', oldNamespace, file[1]).replace('#', '/').upper()
        newObjectName = re.sub(rf'(?i){oldNamespace}', newNamespace, file[1]).replace('#', '/').upper()
        info(rf'Search for {oldObjectName}...')
        for file2 in files:
            filePath = os.path.join(file2[0], file2[1] + file2[2])
            info(rf'> {filePath}')
            if os.path.exists(filePath):
                with open (filePath, 'r+' ) as f:
                    content = f.read()
                    content_new = re.sub(rf'(?i){oldObjectName}', newObjectName, content, flags = re.MULTILINE)
                    if content != content_new:
                        info(rf'>> Occurrences of {oldObjectName} replaced by {newObjectName} in {filePath}')
                        f.seek(0)
                        f.write(content_new)
                        f.truncate()

info('Executed successfully.')

input('Press any key to exit...')