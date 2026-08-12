import os
import shutil

categories = {
    "images" : [".jpg",".png",".jpeg"],
    "videos" : [".mp3",".mp4"],
    "Word" : [".docx"],
    "Presentations" : [".pptx"],
    "Exel" : [".xlsx"]

}

for x in categories:
    if not os.path.exists(x):
        os.makedirs(x)

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

print("Files Organized Successfully")