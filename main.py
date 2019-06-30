from os import walk
from os import path

from area_extractor import parsePBFFile

INPUT_FOLDER = "input"
OUTPUT_FILE = "output.json"


# Main function
def main():
    print("***** Area extractor started *****")
    print("Reading input directory...")

    pbfFiles = getPBFInputFiles(INPUT_FOLDER)
    fileNumber = len(pbfFiles)

    print(f"{fileNumber} PBF file(s) found")

    if fileNumber < 1:
        print("Terminating")
        exit(1)

    for pbfFile in pbfFiles:
        print(f"Processing \"{pbfFile}\"...")
        geoJson = parsePBFFile(pbfFile)

        with open(OUTPUT_FILE, 'w+') as outputFile:
            outputFile.write(geoJson)

        print(f"Wrote output file {OUTPUT_FILE}")

    print("Completed")


def getPBFInputFiles(inputPath):
    pbfFiles = []

    for (dirPath, dirNames, fileNames) in walk(inputPath):
        for fileName in fileNames:
            if fileName.endswith(".pbf"):
                pbfFiles.append(path.join(dirPath, fileName))

    return pbfFiles


if __name__ == '__main__':
    main()
