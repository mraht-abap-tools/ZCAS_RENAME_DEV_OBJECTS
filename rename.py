import re
import os
import sys
import fileinput

pathToGitFolder = input("Pfad zum Git-Ordner: ") + "\src"
oldNamespace = input("Alter Namensraum: ")
newNamespace = input("Neuer Namensraum: ")

oldNamespace = oldNamespace.replace('/', '#').lower()
newNamespace = newNamespace.replace('/', '#').lower()

files = []
for r, d, f in os.walk(pathToGitFolder):
    for file in f:
        files.append([r, file])
        if "test.txt" in file:
            filePath = os.path.join(r, file)
            for i, line in enumerate(fileinput.input(filePath, inplace=1)):
                sys.stdout.write(line.replace(oldNamespace, newNamespace)) # replace

for file in files:
    filepath = file[0]
    filename = file[1]
    
    if re.search(rf'(?i){oldNamespace}', filename):
       newFilename = file.replace(oldNamespace, newNamespace)
       print(rf"Rename file {file} to {newFilename}")
       
       # Rename file
       newFilepath = os.path.join(file[0], newFilename)
       os.rename(filepath, newFilepath)

       # Rename occurences within files
       for file2 in files:
            for i, line in enumerate(fileinput.input(file2, inplace=1)):
                sys.stdout.write(line.replace(oldNamespace, newNamespace)) # replace
