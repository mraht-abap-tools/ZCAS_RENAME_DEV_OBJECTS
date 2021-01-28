import csv
import os
import re
import shutil

pathToGitFolder = input("Path to abapGit repo: ") + "\\src"
while not os.path.isdir(pathToGitFolder):
    print("Entered folder doesn't exist.")
    pathToGitFolder = input("Path to abapGit repo: ") + "\\src"
oldNamespace = input("Old namespace: ")
newNamespace = input("New namespace: ")

excludedObjectsFile = open('exclude.csv', 'r')
excludedObjects = excludedObjectsFile.read()
excludedObjectsFile.close()

oldNamespace = oldNamespace.replace('/', '#').lower()
newNamespace = newNamespace.replace('/', '#').lower()

print('1) Determine relevant files...')
files = []
filesToRename = []

for r, d, f in os.walk(pathToGitFolder):
    for file in f:
        if not re.search(rf'(?i)\.bak', file) and re.search(rf'(?i)({oldNamespace}|{newNamespace})', file):
            filePath = r
            fileSegments = re.search(r'^([\w#]+)(\..+)$',file)
            fileName = fileSegments.group(1)
            fileExtension = fileSegments.group(2)

            newFilename = fileName.replace(oldNamespace, newNamespace)
            if not (re.search(rf'(?i)({fileName}|{newFilename})', excludedObjects)):
                filesToRename.append([filePath, fileName, fileExtension])
            else:
                newFilename = fileName
                print(rf'Exclude {fileName} and {newFilename} from renaming')

            files.append([filePath, newFilename, fileExtension])

print('2) Renaming files...')
for file in filesToRename:
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

print('3) Renaming occurrences within files...')
for file in filesToRename:
    oldObjectName = file[1].replace(newNamespace, oldNamespace).replace('#', '/').upper()
    newObjectName = file[1].replace(oldNamespace, newNamespace).replace('#', '/').upper()
    for file2 in files:
        filePath = os.path.join(file2[0], file2[1] + file2[2])
        print(rf'Search for {oldObjectName} in {filePath}...')
        if os.path.exists(filePath):
            with open (filePath, 'r+' ) as f:
                content = f.read()
                content_new = re.sub(rf'(?i){oldObjectName}', newObjectName, content, flags = re.MULTILINE)
                f.seek(0)
                f.write(content_new)
                f.truncate()

input('Press any key to exit')