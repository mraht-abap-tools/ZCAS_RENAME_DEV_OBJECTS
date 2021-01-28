import re
import os
import sys
import fileinput
import shutil

pathToGitFolder = input("Pfad zum Git-Ordner: ") + "\src"
oldNamespace = input("Alter Namensraum: ")
newNamespace = input("Neuer Namensraum: ")

while not os.path.isdir(pathToGitFolder):
    print("Angegebener Ordner existiert nicht oder ist kein abapGit-Repo.")
    pathToGitFolder = input("Pfad zum Git-Ordner: ") + "\src"

oldNamespace = oldNamespace.replace('/', '#').lower()
newNamespace = newNamespace.replace('/', '#').lower()

files = []
for r, d, f in os.walk(pathToGitFolder):
    for file in f:
        if not re.search(rf'(?i)\.bak', file) and (re.search(rf'(?i){oldNamespace}', file) or re.search(rf'(?i){newNamespace}', file)):
            filePath = r
            fileSegments = re.search(r'^([\w#]+)(\..+)$',file)
            fileName = fileSegments.group(1)
            fileExtension = fileSegments.group(2)
            files.append([filePath, fileName, fileExtension])

print('1) Renaming files...')
for file in files:
    filePath = file[0]
    fileName = file[1]
    fileExtension = file[2]
    newFilename = ''

    if re.search(rf'(?i){oldNamespace}', fileName):
        newFilename = fileName.replace(oldNamespace, newNamespace)

        oldFilepath = os.path.join(filePath, fileName + fileExtension)
        newFilepath = os.path.join(filePath, newFilename + fileExtension)
        if shutil.move(oldFilepath, newFilepath):
            file[1] = newFilename
            print(rf'{fileName} => {newFilename}')
        else:
            print(rf'Error: {fileName} => {newFilename}')
        
    elif re.search(rf'(?i){newNamespace}', fileName):
        newFilename = fileName

# Rename occurences within files
print('2) Renaming occurrences within files...')
for file in files:
    oldObjectName = file[1].replace(newNamespace, oldNamespace).replace('#', '/').upper()
    newObjectName = file[1].replace(oldNamespace, newNamespace).replace('#', '/').upper()
    for file2 in files:
        filePath = os.path.join(file2[0], file2[1] + file2[2])
        print(rf'Search in {filePath}...')
        if os.path.exists(filePath):
            with open (filePath, 'r+' ) as f:
                content = f.read()
                content_new = re.sub(rf'(?i){oldObjectName}', newObjectName, content, flags = re.MULTILINE)
                f.seek(0)
                f.write(content_new)
                f.truncate()

print('Done.')