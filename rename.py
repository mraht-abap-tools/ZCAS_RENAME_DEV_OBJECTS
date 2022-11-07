# Version: 18.10.2022-001

import logging
import os
import re
import shutil

def info(msg):
    logging.info(msg)
    print(msg)

def error(msg):
    logging.error(msg)
    print(msg)

def replace(m, oldNamespace, newNamespace):
    newStr = re.sub(oldNamespace, newNamespace, m.group(), flags = re.IGNORECASE)
    return newStr.lower() if m.group().islower() else newStr.upper()

def execute():
    info('************************************* ZCAS_RENAME_DEV_OBJECTS **************************************')
    print(f"Enter 'quit' or 'STRG+C' to quit\n")
    pathToGitFolder = input("Path to abapGit repo: ")
    while not os.path.isdir(pathToGitFolder + "\\src") and not pathToGitFolder == 'quit':
        print("Entered folder doesn't exist or isn't an abapGit repository.")
        pathToGitFolder = input("Path to abapGit repo: ")
    if pathToGitFolder == 'quit': return False
    oldNamespace = input("Old namespace: ")
    if oldNamespace == 'quit': return False
    newNamespace = input("New namespace: ")
    if newNamespace == 'quit': return False
    overwrite = input("Overwrite (y/n)? ")
    if overwrite == 'quit': return False

    logging.basicConfig(level=logging.DEBUG, filename="log.txt", filemode="a+",
                        format="%(asctime)-15s %(levelname)-8s %(message)s")

    info('****************************************************************************************************')

    info('1) Copy files and prepare renaming...')
    newNamespace       = newNamespace.replace('/', '#').lower()
    oldNamespaceObject = oldNamespace
    oldNamespaceFile   = oldNamespace.replace('/', '#').lower()

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

    info('\n2) Determine relevant files...')
    files = []
    filesToRename = []

    for filePath, dirnames, filenames in os.walk(newPathToGitFolder):
        for file in filenames:
            fileSegments = re.search(f'^(([\w#]+)[\.\w#\s]+)(\..+)$',file)
            if fileSegments is not None:
                fileName = fileSegments.group(1)
                objectName = fileSegments.group(2)
                fileExtension = fileSegments.group(3)        
            if not re.search(f'(?i)\.bak', file) and re.search(rf'(?i)({oldNamespaceFile}|{newNamespace})', file):
                newFilename = re.sub(f'(?i){oldNamespaceFile}', newNamespace, fileName)
                if excludedObjectsFile is None or not (re.search(rf'(?i){fileName}', excludedObjects)):
                    filesToRename.append([filePath, fileName, fileExtension, objectName])
                    files.append([filePath, newFilename, fileExtension, objectName])
                else:
                    info(f'Exclude {fileName} and {newFilename} from renaming')
                    newFilename = fileName
            else:
                files.append([filePath, fileName, fileExtension, objectName])

    info('\n3) Renaming files...')
    for file in filesToRename:
        filePath = file[0]
        fileName = file[1]
        fileExtension = file[2]
        objectName = file[3]

        newFilename = ''
        newObjectName = ''

        if re.search(f'(?i){oldNamespaceFile}', fileName):
            newFilename = re.sub(f'(?i){oldNamespaceFile}', newNamespace, fileName)
            newObjectName = re.sub(f'(?i){oldNamespaceFile}', newNamespace, objectName)
            oldFilepath = os.path.join(filePath, fileName + fileExtension)
            newFilepath = os.path.join(filePath, newFilename + fileExtension)

            try:
                shutil.move(oldFilepath, newFilepath)
                file[1] = newFilename
                file[3] = newObjectName
                info(f'{fileName}{fileExtension} => {newFilename}{fileExtension}')
            except BaseException:
                error(f'Error: Renaming {fileName} to {newFilename} failed.')
            
        elif re.search(f'(?i){newNamespace}', fileName):
            newFilename = fileName

    info('\n4) Renaming occurrences within files...')
    for index, file in enumerate(files):
        print('%-50s' % file[1] + f': {round((index / len(files)) * 100, 2)}%',"\r", end=' ')
        filePath = os.path.join(file[0], file[1] + file[2])
        
        if os.path.exists(filePath):
            with open (filePath, 'r+', encoding="utf8") as f:
                try:
                    content = f.read()
                except BaseException:
                    continue

                content_new = re.sub(f'(?i){oldNamespaceObject}', lambda m: replace(m, oldNamespaceObject, newNamespace), content, flags = re.MULTILINE)
                if content != content_new:
                    info(f'>> Occurrences of "{oldNamespaceObject}" replaced by "{newNamespace}" in {filePath}')
                    f.seek(0)
                    f.write(content_new)
                    f.truncate()

    info('\n\n5) Renaming directories...')
    for filePath, dirnames, filenames in os.walk(newPathToGitFolder, topdown = False):
        for dir in dirnames:
            newDir = re.sub(f'(?i){oldNamespaceFile}', newNamespace, dir)
            oldDirpath = os.path.join(filePath, dir)
            newDirpath = os.path.join(filePath, newDir)        
            try:
                shutil.move(oldDirpath, newDirpath)
                info(f'{dir} => {newDir}')
            except BaseException:
                error(f'Error: Renaming {dir} to {newDir} failed.')

    if overwrite == 'y':
        info('\n6) Overwrite files and directories...')
        shutil.rmtree(pathToGitFolder)
        shutil.copytree(newPathToGitFolder, pathToGitFolder, dirs_exist_ok=True)
        shutil.rmtree(newPathToGitFolder)

    info(f'\nRenaming {oldNamespaceFile} / {oldNamespaceObject} => {newNamespace} was successful.\n')
    return True

runApp = True
while runApp == True:
    runApp = execute()
