import os
import shutil

def create_folders(categories):
    for x in categories:
        if not os.path.exists(x):
            os.makedirs(x)
def arrange_files(categories):
    for file in os.listdir('.'):
        if os.path.isfile(file):
            name, ext = os.path.splitext(file)
            ext = ext.lower()
            for category, extensions in categories.items():
                if ext in extensions:
                    print(category)
                    shutil.move(file, category)
                    break
        else:
                print("Unknown Extension!")

def main():
 categories = {
    "images" : [".jpg",".png",".jpeg"],
    "videos" : [".mp3",".mp4"],
    "Word" : [".docx"],
    "Presentations" : [".pptx"],
    "Exel" : [".xlsx"]
}
 create_folders(categories)
 arrange_files(categories)

print("Files Organized Successfully")


if "__name__" == "__main__":
    main()