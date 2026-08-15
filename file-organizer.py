import os
import shutil
from google import genai

def create_folders(categories, ai_categories):
    for x in categories:
        if not os.path.exists(x):
            os.makedirs(x)

    for x in ai_categories:
        if not os.path.exists(x):
            os.makedirs(x)
def arrange_files(categories, ai_categories):
    ignored_folders = set(categories) | set(ai_categories)
    ignored_files = {"file-organizer.py", "README.md"}
    for file in os.listdir('.'):
        if not os.path.isfile(file):
            continue
        if file in ignored_folders or file in ignored_files:
            continue
        name, ext = os.path.splitext(file)
        ext = ext.lower()
        for category, extensions in categories.items():
                if ext in extensions:
                    print(category)
                    shutil.move(file, category)
                    break
        else:
                category = classify_file(file, ai_categories)
                if category in ai_categories:
                    print(f"{file} ➡ {category}")
                    shutil.move(file, category)

def classify_file(file_name, ai_categories):
    client = genai.Client()
    prompt = (f"""You are an intelligent file organization assistant.

Your task is to decide which folder is the BEST place to organize the given file.

File name:
{file_name}

Available folders:
{ai_categories}

Important:
- Choose ONLY ONE folder.
- Choose the folder that represents the file's PRIMARY context or purpose.
- Do not choose a category simply because the file may be related to it.
- Consider where a user would most naturally look for this file later.
- Academic/university work should belong to University when its primary context is education.
- A personal or independent project should belong to Project.
- A financial document should belong to Finance when finance is its primary purpose.
- If multiple categories seem relevant, choose the one that best represents the file's primary organizational context.

Rules:
- Return ONLY ONE value.
- Your answer MUST be exactly one category from the provided list.
- If none of the categories is an appropriate match, return exactly:
Unknown
- Do NOT provide explanations.
- Do NOT add punctuation or extra words.""")
    response = client.models.generate_content(
        model = "gemini-3.6-flash",
        contents = prompt
    )
    category = response.text.strip()
    if category in ai_categories:
        return category
    elif category == "Unknown":
         print("AI could not find a suitable category")
    else:
        print("Unexpected AI Response: ", response.text)

def main():
 categories = {
    "images" : [".jpg",".png",".jpeg"],
    "videos" : [".mp3",".mp4"],
    "Word" : [".docx"],
    "Presentations" : [".pptx"],
    "Exel" : [".xlsx"]
}
 ai_categories = ["University","Work","Project","Personal","Finance"]

 client = genai.Client()
 print("Gen AI Connected!")
 
 create_folders(categories, ai_categories)
 arrange_files(categories, ai_categories)

 print("Files Organized Successfully")


if __name__ == "__main__":
    main()