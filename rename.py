# Version: 18.10.2022-001
#
# TODO:
# - [NEW] FUGR: In case of new namespace with '/', prefixes 'L' or 'SAPL' have to be set after the last '/' of the new namespace,
#               e.g. 'LZIAL_T_CNF_VARF00 => #CAS#LEWM_T_CNF_VARF00, not L#CAS#EWM_T_CNF_VARF00

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

def inputPathToGitFolder():
    pathToGitFolder = ''
    while pathToGitFolder == '':
        pathToGitFolder = input("Path to abapGit repo: ")
        if pathToGitFolder == 'quit' or pathToGitFolder == 'exit':
            exit()
        elif not os.path.isdir(pathToGitFolder + "\\src"):
            pathToGitFolder = ''
            print("Entered folder doesn't exist or isn't an abapGit repository.")
    return pathToGitFolder

def inputOldNamespace():
    oldNamespace = ''
    while oldNamespace == '':
        oldNamespace = input("Old namespace: ")
        if oldNamespace == 'quit' or oldNamespace == 'exit':
            exit()
    return oldNamespace

def inputNewNamespace(oldNamespace):
    newNamespace = ''
    while newNamespace == '':
        newNamespace = input("New namespace: ")
        if newNamespace == 'quit' or newNamespace == 'exit':
            exit()
        elif newNamespace == oldNamespace:
            newNamespace = ''
            print("Entered new namespace is not different from old namespace.")
    return newNamespace

def inputOverwrite():
    overwrite = ''
    while overwrite == '':
        overwrite = input("Overwrite existing files (y/n)? ")
        if overwrite == 'quit' or overwrite == 'exit':
            exit()
        elif not re.search('(?i)^[jyn]+$', overwrite):
            overwrite = ''
            print("Please enter 'y' or 'n'.")
    return overwrite

def execute():
    info('************************************* ZCAS_RENAME_DEV_OBJECTS **************************************')
    print(f"Enter 'quit' or 'STRG+C' to quit\n")

    pathToGitFolder = inputPathToGitFolder()
    oldNamespace    = inputOldNamespace()
    newNamespace    = inputNewNamespace(oldNamespace)
    overwrite       = inputOverwrite()

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
            fileSegments = re.search(f'^(([\w#]+)[\.\w#\s]+)(\..+)$', file)
            ##fileSegments = re.search(f'^([\w#]+)(\.fugr\.([\w#]+))?(\..+)$', file)
            if fileSegments is not None:
                fileName = fileSegments.group(1)
                objectName = fileSegments.group(2)
                fileExtension = fileSegments.group(3)

            if not re.search(f'(?i)\.bak', file) and re.search(rf'(?i)({oldNamespaceFile}|{newNamespace})', file):
                
                sapObjectSegments = re.search(f'(?i)(\.fugr\.)(#?[\w]+#?(SAPL|L)\w+)', file)
                if sapObjectSegments != None:
                    sapObjectName   = sapObjectSegments.group(2)
                    sapObjectPrefix = sapObjectSegments.group(3)
                    t1 = sapObjectSegments.start(3)
                    t2 = sapObjectSegments.end(3)
                    ##TODO Split and concentenate string
                    if '#' in sapObjectName:
                        newSAPObjectName = re.sub(f'(?i){sapObjectName}', newNamespace, fileName)
                    else:
                        newSAPObjectName = re.sub(f'(?i){sapObjectName}', newNamespace, fileName)
                    newFilename = re.sub(f'(?i){oldNamespaceFile}', newNamespace, fileName)
                else:
                    newFilename = re.sub(f'(?i){oldNamespaceFile}', newNamespace, fileName)

                if excludedObjectsFile is None or not (re.search(rf'(?i){fileName}', excludedObjects)):
                    filesToRename.append([filePath, fileName, fileExtension, objectName])
                    files.append([filePath, newFilename, fileExtension, objectName])
                else:
                    info(f'Excluded {fileName} and {newFilename} from renaming')
                    ##Obsolete? newFilename = fileName
            else:
                files.append([filePath, fileName, fileExtension, objectName])

    info('\n3) Renaming files...')
    for file in filesToRename:
        filePath = file[0]
        fileName = file[1]
        fileExtension = file[2]
        objectName = file[3]

        newFilename    = ''
        newObjectName  = ''

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

    info('\n5) Renaming occurrences within files...')
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

    info('\n\n6) Renaming directories...')
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
        info('\n7) Overwrite files and directories...')
        shutil.rmtree(pathToGitFolder)
        shutil.copytree(newPathToGitFolder, pathToGitFolder, dirs_exist_ok=True)
        shutil.rmtree(newPathToGitFolder)

    info(f'\nRenaming {oldNamespaceFile} / {oldNamespaceObject} => {newNamespace} was successful.\n')
    return True

runApp = True
while runApp == True:
    runApp = execute()
