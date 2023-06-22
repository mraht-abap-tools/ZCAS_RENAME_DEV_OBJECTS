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
    pathToGitFolder = ['', '']
    while pathToGitFolder[0] == '':
        pathToGitFolder[0] = input("Path to abapGit repo: ")
        if pathToGitFolder[0] == 'quit' or pathToGitFolder[0] == 'exit':
            exit()
        elif not os.path.isdir(pathToGitFolder[0] + "\\src"):
            pathToGitFolder[0] = ''
            print("Entered folder doesn't exist or isn't an abapGit repository.")
    pathToGitFolder[1]  = pathToGitFolder[0] + '\src_renamed'
    pathToGitFolder[0] += '\src'
    return pathToGitFolder

def inputOldNamespace():
    oldNamespace = ['', '']
    while oldNamespace[0] == '':
        oldNamespace[0] = input("Old namespace: ").lower()
        if oldNamespace[0] == 'quit' or oldNamespace[0] == 'exit':
            exit()
    oldNamespace[1] = oldNamespace[0].replace('/', '#')
    return oldNamespace

def inputNewNamespace(oldNamespace):
    newNamespace = ['', '']
    while newNamespace[0] == '':
        newNamespace[0] = input("New namespace: ").lower()
        if newNamespace[0] == 'quit' or newNamespace[0] == 'exit':
            exit()
        elif newNamespace[0] == oldNamespace[0]:
            newNamespace[0] = ''
            print("Entered new namespace is not different from old namespace.")
    newNamespace[1] = newNamespace[0].replace('/', '#')
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
    overwrite = False if re.search('(?i)n', overwrite) else True
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

def copyFiles(pathToGitFolder):
    shutil.copytree(pathToGitFolder[0], pathToGitFolder[1], dirs_exist_ok=True)

def det_files_and_objects(pathToGitFolder, oldNamespace, newNamespace, excludedObjects):
    filesToRename   = []
    objectsToRename = []

    for filePath, dirnames, filenames in os.walk(pathToGitFolder[1]):
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

            if re.search(f'(?i)\.bak', file) or not re.search(rf'(?i)({oldNamespace[1]}|{newNamespace[1]})', file):
                filesToRename.append([False, filePath, fileName, newFilename, fileExtension])
                continue
                
            oldTopObjectName = ''
            newTopObjectName = ''

            sapObjectSegments = re.search(f'(?i)({oldNamespace[1]}(\w+)\.fugr\.){oldNamespace[1]}((L|SAPL)(\w+))', fileName)
            if sapObjectSegments != None:
                topObjectName   = sapObjectSegments.group(2)
                sapObjectPrefix = sapObjectSegments.group(4)
                
                if '#' in oldNamespace[1] and '#' not in newNamespace[1]:
                    ## Renaming from '/' to '[A-Z]'
                    oldTopObjectName = oldNamespace[1] + sapObjectPrefix + topObjectName
                    newTopObjectName = sapObjectPrefix + newNamespace[1] + topObjectName
                else:
                    ## Renaming from '[A-Z]' to '/'
                    oldTopObjectName = sapObjectPrefix + oldNamespace[1] + topObjectName
                    newTopObjectName = newNamespace[1] + sapObjectPrefix + topObjectName
            
            if oldTopObjectName != '' and newTopObjectName != '':
                newFilename = re.sub(f'(?i){oldTopObjectName}', newTopObjectName, newFilename)

                oldTopObjectName = oldTopObjectName.replace('#', '/')
                newTopObjectName = newTopObjectName.replace('#', '/')
                object = [oldTopObjectName, newTopObjectName]
                if object not in objectsToRename:
                    objectsToRename.append(object)

            newFilename = re.sub(f'(?i){oldNamespace[1]}', newNamespace[1], newFilename)
            fileToRename = [True, filePath, fileName, newFilename, fileExtension]
            if fileToRename not in filesToRename:
                filesToRename.append(fileToRename)
 
    objectsToRename.append([oldNamespace[0], newNamespace[0]])

    return filesToRename, objectsToRename

def rename_files(filesToRename, oldNamespace):
    for file in filesToRename: 
        if file[0] == False:
            continue

        filePath      = file[1]
        fileName      = file[2]
        newFilename   = file[3]
        fileExtension = file[4]

        if re.search(f'(?i){oldNamespace[1]}', fileName):
            oldFilepath = os.path.join(filePath, fileName    + fileExtension)
            newFilepath = os.path.join(filePath, newFilename + fileExtension)

            try:
                shutil.move(oldFilepath, newFilepath)
                info(f'{fileName}{fileExtension} => {newFilename}{fileExtension}')
            except BaseException:
                error(f'Error: Renaming {fileName} to {newFilename} failed.')

    return filesToRename

def rename_objects(filesToRename, objectsToRename):
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

def rename_directories(pathToGitFolder, oldNamespace, newNamespace):
    for filePath, dirnames, filenames in os.walk(pathToGitFolder[1], topdown = False):
        for dir in dirnames:
            newDir = re.sub(f'(?i){oldNamespace[1]}', newNamespace[1], dir)
            oldDirpath = os.path.join(filePath, dir)
            newDirpath = os.path.join(filePath, newDir)        
            try:
                shutil.move(oldDirpath, newDirpath)
                info(f'{dir} => {newDir}')
            except BaseException:
                error(f'Error: Renaming {dir} to {newDir} failed.')

def overwrite_files(overwrite, pathToGitFolder):
    if overwrite == True:
        shutil.rmtree(pathToGitFolder[0])
        shutil.copytree(pathToGitFolder[1], pathToGitFolder[0], dirs_exist_ok=True)
        shutil.rmtree(pathToGitFolder[1])
    else:
        info(f'=> User turned overwriting off.')

def execute():
    logging.basicConfig(level=logging.DEBUG, filename="log.txt", filemode="a+",
                        format="%(asctime)-15s %(levelname)-8s %(message)s")

    info('************************************* ZCAS_RENAME_DEV_OBJECTS **************************************')
    print(f"Enter 'quit' or 'STRG+C' to quit\n")

    pathToGitFolder    = inputPathToGitFolder()
    oldNamespace       = inputOldNamespace()
    newNamespace       = inputNewNamespace(oldNamespace)
    overwrite          = inputOverwrite()

    excludedObjects = buildExcludeFiles()

    info('****************************************************************************************************')

    info(f'1) Copy files and prepare renaming...')
    copyFiles(pathToGitFolder)

    info(f'\n2) Determine new names...')
    filesToRename, objectsToRename = det_files_and_objects(pathToGitFolder, oldNamespace, newNamespace, excludedObjects)

    info(f'\n3) Renaming files...')
    filesToRename = rename_files(filesToRename, oldNamespace)

    info(f'\n4) Renaming objects within files...')
    rename_objects(filesToRename, objectsToRename)

    info(f'\n5) Renaming directories...')
    rename_directories(pathToGitFolder, oldNamespace, newNamespace)

    info(f'\n6) Overwrite files and directories...')
    overwrite_files(overwrite, pathToGitFolder)

    info(f'\nRenaming \'{oldNamespace[0]}\' (\'{oldNamespace[1]}\')  =>  \'{newNamespace[0]}\' (\'{newNamespace[1]}\') was successful.\n')
    return True

runApp = True
while runApp == True:
    runApp = execute()
