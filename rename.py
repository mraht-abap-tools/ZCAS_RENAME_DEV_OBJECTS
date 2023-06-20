# Version: 20.06.2023-001

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
        overwrite = input("Overwrite existing filesToRename (y/n)? ")
        if overwrite == 'quit' or overwrite == 'exit':
            exit()
        elif not re.search('(?i)^[jyn]+$', overwrite):
            overwrite = ''
            print("Please enter 'y' or 'n'.")
    return overwrite

def buildExcludeFiles():
    excludedObjects     = None
    excludedObjectsFile = None
    if os.path.exists('exclude.csv'):
        excludedObjectsFile = open('exclude.csv', 'r')
        excludedObjects = excludedObjectsFile.read()
        excludedObjectsFile.close()
        excludedObjects = excludedObjects.replace('/', '#').upper()

    return excludedObjects

def copyFiles(pathToGitFolder, newPathToGitFolder):
    shutil.copytree(pathToGitFolder, newPathToGitFolder, dirs_exist_ok=True)

def det_files_and_objects(newPathToGitFolder, oldNamespace, oldNamespaceFile, newNamespace, newNamespaceFile, excludedObjects):
    filesToRename   = []
    objectsToRename = []

    for filePath, dirnames, filenames in os.walk(newPathToGitFolder):
        for file in filenames:
            fileSegments = re.search(f'^(([\w#]+)[\.\w#\s]+)(\..+)$', file)
            if fileSegments is None:
                continue

            fileName         = fileSegments.group(1)
            newFilename      = fileName
            fileExtension    = fileSegments.group(3)

            if excludedObjects is not None and re.search(rf'(?i){fileName}', excludedObjects):
                info(f'Excluded {fileName} from processing')
                continue

            if re.search(f'(?i)\.bak', file) or not re.search(rf'(?i)({oldNamespaceFile}|{newNamespaceFile})', file):
                filesToRename.append([False, filePath, fileName, newFilename, fileExtension])
                continue
                
            oldTopObjectName = ''
            newTopObjectName = ''

            sapObjectSegments = re.search(f'(?i)({oldNamespaceFile}(\w+)\.fugr\.){oldNamespaceFile}((L|SAPL)(\w+))', fileName)
            if sapObjectSegments != None:
                topObjectName   = sapObjectSegments.group(2)
                sapObjectPrefix = sapObjectSegments.group(4)
                
                if '#' in oldNamespaceFile and '#' not in newNamespaceFile:
                    ## Renaming from '/' to '[A-Z]'
                    oldTopObjectName = oldNamespaceFile + sapObjectPrefix + topObjectName
                    newTopObjectName = sapObjectPrefix + newNamespaceFile + topObjectName
                else:
                    ## Renaming from '[A-Z]' to '/'
                    oldTopObjectName = sapObjectPrefix + oldNamespaceFile + topObjectName
                    newTopObjectName = newNamespaceFile + sapObjectPrefix + topObjectName
            
            if oldTopObjectName != '' and newTopObjectName != '':
                newFilename = re.sub(f'(?i){oldTopObjectName}', newTopObjectName, newFilename)

                oldTopObjectName = oldTopObjectName.replace('#', '/')
                newTopObjectName = newTopObjectName.replace('#', '/')
                object = [oldTopObjectName, newTopObjectName]
                if object not in objectsToRename:
                    objectsToRename.append(object)

            newFilename = re.sub(f'(?i){oldNamespaceFile}', newNamespaceFile, newFilename)
            fileToRename = [True, filePath, fileName, newFilename, fileExtension]
            if fileToRename not in filesToRename:
                filesToRename.append(fileToRename)
 
    objectsToRename.append([oldNamespace, newNamespace])

    return filesToRename, objectsToRename

def rename_files(filesToRename, oldNamespaceFile):
    for file in filesToRename: 
        if file[0] == False:
            continue

        filePath      = file[1]
        fileName      = file[2]
        newFilename   = file[3]
        fileExtension = file[4]

        if re.search(f'(?i){oldNamespaceFile}', fileName):
            oldFilepath = os.path.join(filePath, fileName    + fileExtension)
            newFilepath = os.path.join(filePath, newFilename + fileExtension)

            try:
                shutil.move(oldFilepath, newFilepath)
                info(f'{fileName}{fileExtension} => {newFilename}{fileExtension}')
            except BaseException:
                error(f'Error: Renaming {fileName} to {newFilename} failed.')

    return filesToRename

def rename_objects(filesToRename, objectsToRename, oldNamespaceObject, newNamespace):
    for index, file in enumerate(filesToRename):
        print('%-50s' % file[3] + f': {round((index / (len(filesToRename) * len(objectsToRename))) * 100, 2)}%',"\r", end=' ')
        filePath = os.path.join(file[1], file[3] + file[4])

        if os.path.exists(filePath):
            with open (filePath, 'r+', encoding="utf8") as f:
                try:
                    content = f.read()
                    newContent = content

                    for object in objectsToRename:
                        oldObject = object[0]
                        newObject = object[1]
                        
                        tmpContent = re.sub(f'(?i){oldObject}', lambda m: replace(m, oldObject, newObject), newContent, flags = re.MULTILINE)
                        if tmpContent != newContent:
                            info(f'>> Occurrences of "{oldObject}" replaced by "{newObject}" in {filePath}')
                        newContent = tmpContent
                
                    if content != newContent:
                        f.seek(0)
                        f.write(newContent)
                        f.truncate()

                except BaseException:
                    error(f'Error: Renaming objects in file {filePath} failed.')

    info(f'\n')

def rename_directories(pathToGitFolder, newPathToGitFolder, oldNamespaceFile, newNamespace, overwrite):
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

def overwrite_files(overwrite, pathToGitFolder, newPathToGitFolder):
    if overwrite == True:
        shutil.rmtree(pathToGitFolder)
        shutil.copytree(newPathToGitFolder, pathToGitFolder, dirs_exist_ok=True)
        shutil.rmtree(newPathToGitFolder)
    else:
        info(f'=> User turned overwriting off.')

def execute():
    logging.basicConfig(level=logging.DEBUG, filename="log.txt", filemode="a+",
                        format="%(asctime)-15s %(levelname)-8s %(message)s")

    info('************************************* ZCAS_RENAME_DEV_OBJECTS **************************************')
    print(f"Enter 'quit' or 'STRG+C' to quit\n")

    pathToGitFolder    = inputPathToGitFolder()
    newPathToGitFolder = pathToGitFolder + '\src_renamed'
    pathToGitFolder   += '\src'
    oldNamespace       = inputOldNamespace()
    oldNamespaceFile   = oldNamespace.replace('/', '#').lower()
    newNamespace       = inputNewNamespace(oldNamespace).lower()
    newNamespaceFile   = newNamespace.replace('/', '#')
    overwrite          = inputOverwrite()

    excludedObjects = buildExcludeFiles()

    info('****************************************************************************************************')

    info(f'1) Copy files and prepare renaming...')
    copyFiles(pathToGitFolder, newPathToGitFolder)

    info(f'\n2) Determine new names...')
    filesToRename, objectsToRename = det_files_and_objects(newPathToGitFolder, oldNamespace, oldNamespaceFile, newNamespace, newNamespaceFile, excludedObjects)

    info(f'\n3) Renaming files...')
    filesToRename = rename_files(filesToRename, oldNamespaceFile)

    info(f'\n4) Renaming objects within files...')
    rename_objects(filesToRename, objectsToRename, oldNamespace, newNamespace)

    info(f'\n5) Renaming directories...')
    rename_directories(pathToGitFolder, newPathToGitFolder, oldNamespaceFile, newNamespaceFile, overwrite)

    info(f'\n6) Overwrite files and directories...')
    overwrite_files(overwrite, pathToGitFolder, newPathToGitFolder)

    info(f'\nRenaming \'{oldNamespace}\' (\'{oldNamespaceFile}\')  =>  \'{newNamespace}\' (\'{newNamespaceFile}\') was successful.\n')
    return True

runApp = True
while runApp == True:
    runApp = execute()
