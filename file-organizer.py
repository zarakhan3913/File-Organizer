import os
import shutil
import json
from google import genai

def create_folders(ai_categories):
    for x in ai_categories:
        if not os.path.exists(x):
            os.makedirs(x)

def save_categories(ai_categories):
    with open("ai_categories.json","w") as file:
        json.dump(ai_categories, file, indent=4)

def load_categories():
    with open("ai_categories.json","r") as file:
        return json.load(file)

def arrange_files(ai_categories):
    ignored_folders =  set(ai_categories)
    ignored_files = {"file-organizer.py", "README.md"}

    for file in os.listdir('.'):
        if not os.path.isfile(file):
            continue

        if file in ignored_folders or file in ignored_files:
            continue

        _, ext = os.path.splitext(file)
        ext = ext.lower()
        category = classify_file(file, ext, ai_categories)
        if category in ai_categories:
            print(f"{file} ➡ {category}")
            shutil.move(file, category)
                    

def classify_file(file_name, ext,  ai_categories):
    client = genai.Client()
    prompt = (f"""You are an intelligent file organization assistant.

Your task is to decide which folder is the BEST place to organize the given file.

File name:
{file_name}

Extension: 
{ext}

Available folders:
{ai_categories}

Important:
- Choose ONLY ONE folder.
- Choose the folder that represents the file's PRIMARY context or purpose.
- Do not choose a category simply because the file may be related to it.
- Consider where a user would most naturally look for this file later.
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
         print(f"AI could not find a suitable category for: {file_name}")
         return "Unknown"
    else:
        print("Unexpected AI Response: ", response.text)
        return "Unknown"

def add_categories(ai_categories):
    user_categories = input(
    "Enter your categories separated by commas: "
).split(",")
    user_categories = [
    category.strip()
    for category in user_categories
    if category.strip()
]
    ai_categories.extend(user_categories)
    save_categories(ai_categories)

def main():
 if os.path.exists("ai_categories.json"):
     ai_categories = load_categories()
     choice = input("Do you want to add new categories? (y/n)").lower()
     if choice == 'y':
          add_categories(ai_categories)
     elif choice == 'n':
          pass
     else:
          print("Invalid choice")
          return
 else:
    ai_categories = []
    add_categories(ai_categories)

    print(f"Categories : {ai_categories}")

 create_folders(ai_categories)
 arrange_files( ai_categories)

 print("Files Organized Successfully")


if __name__ == "__main__":
    main()