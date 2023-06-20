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
        overwrite = input("Overwrite existing files (y/n)? ")
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

def det_relevant_files(newPathToGitFolder, oldNamespaceFile, newNamespace, excludedObjects):
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

            newFilename = ''
            if not re.search(f'(?i)\.bak', file) and re.search(rf'(?i)({oldNamespaceFile}|{newNamespace})', file):

                sapObjectSegments = re.search(f'(?i)([#\w]+)\.fugr\.((#\w+#)?(L|SAPL)(\w+))', fileName)
                if sapObjectSegments != None:
                    sapObjectName        = sapObjectSegments.group(1)
                    sapSubobjectName     = sapObjectSegments.group(2)
                    sapSubobjectNameI1   = sapObjectSegments.start(2)
                    sapSubobjectNameI2   = sapObjectSegments.end(2)

                    sapObjectPrefix   = sapObjectSegments.group(4)
                    sapObjectPrefixI1 = sapObjectSegments.start(4)
                    sapObjectPrefixI2 = sapObjectSegments.end(4)
                    
                    if     '#'     in sapSubobjectName and '#' not in newNamespace \
                        or '#' not in sapSubobjectName and '#'     in newNamespace:
                        newFilename = fileName[:sapObjectPrefixI1] + fileName[sapObjectPrefixI2:]
                        
                        newFilename = newFilename[:sapSubobjectNameI1] + sapObjectPrefix + newFilename[sapSubobjectNameI1:]
                        newFilename = re.sub(f'(?i){oldNamespaceFile}', newNamespace, newFilename)
                
                if newFilename == '':
                    newFilename = re.sub(f'(?i){oldNamespaceFile}', newNamespace, fileName)

                if excludedObjects is None or not (re.search(rf'(?i){fileName}', excludedObjects)):
                    filesToRename.append([filePath, fileName, fileExtension, objectName])
                    files.append([filePath, newFilename, fileExtension, objectName])
                else:
                    info(f'Excluded {fileName} and {newFilename} from renaming')
                    ##Obsolete? newFilename = fileName
            else:
                files.append([filePath, fileName, fileExtension, objectName])

    return files, filesToRename

def rename_files(filesToRename, oldNamespaceFile, newNamespace):
    for file in filesToRename:
        filePath      = file[0]
        fileName      = file[1]
        fileExtension = file[2]
        objectName    = file[3]

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
                file[4] = newObjectName
                info(f'{fileName}{fileExtension} => {newFilename}{fileExtension}')
            except BaseException:
                error(f'Error: Renaming {fileName} to {newFilename} failed.')
            
        elif re.search(f'(?i){newNamespace}', fileName):
            newFilename = fileName

    return filesToRename

def rename_occurrences(files, oldNamespaceObject, newNamespace):
    for index, file in enumerate(files):
        print('%-50s' % file[1] + f': {round((index / len(files)) * 100, 2)}%',"\r", end=' ')
        filePath = os.path.join(file[0], file[1] + file[2])
        
        if os.path.exists(filePath):
            with open (filePath, 'r+', encoding="utf8") as f:
                try:
                    content = f.read()
                except BaseException:
                    continue

                content_new = re.sub(f'{oldNamespaceObject}', lambda m: replace(m, oldNamespaceObject, newNamespace), content, flags = re.MULTILINE)
                content_new = re.sub(f'{file[3]}', lambda m: replace(m, file[3], file[4]), content, flags = re.MULTILINE)
                if content != content_new:
                    info(f'>> Occurrences of "{oldNamespaceObject}" replaced by "{newNamespace}" in {filePath}')
                    f.seek(0)
                    f.write(content_new)
                    f.truncate()

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

    if overwrite == 'y':
        info('\n6) Overwrite files and directories...')
        shutil.rmtree(pathToGitFolder)
        shutil.copytree(newPathToGitFolder, pathToGitFolder, dirs_exist_ok=True)
        shutil.rmtree(newPathToGitFolder)

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

    info('1) Copy files and prepare renaming...')
    copyFiles(pathToGitFolder, newPathToGitFolder)

    info('\n2) Determine relevant files...')
    files, filesToRename = det_relevant_files(newPathToGitFolder, oldNamespaceFile, newNamespaceFile, excludedObjects)

    info('\n3) Renaming files...')
    filesToRename = rename_files(filesToRename, oldNamespaceFile, newNamespaceFile)

    info('\n4) Renaming occurrences within files...')
    rename_occurrences(files, oldNamespace, newNamespace)

    info('\n\n5) Renaming directories...')
    rename_directories(pathToGitFolder, newPathToGitFolder, oldNamespaceFile, newNamespaceFile, overwrite)

    info(f'\nRenaming \'{oldNamespace}\' (\'{oldNamespaceFile}\')  =>  \'{newNamespace}\' (\'{newNamespaceFile}\') was successful.\n')
    return True

runApp = True
while runApp == True:
    runApp = execute()
