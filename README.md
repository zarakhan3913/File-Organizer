# AI-Powered File Organizer

> A privacy-aware Python file organizer that uses Google Gemini to intelligently classify user files into customizable folders. 

---

## Table of Contents

* [Overview](#overview)
* [Problem Statement](#problem-statement)
* [Dataset Description](#dataset-description)
* [Tools & Technologies](#tools--technologies)
* [Methods](#methods)
* [Key Insights](#key-insights)
* [Dashboard / Model / Output](#dashboard--model--output)
* [How to Run This Project](#how-to-run-this-project)
* [Result & Conclusion](#result--conclusion)
* [Future Work](#future-work)
* [Author & Contact](#author--contact)

---

## Overview

The **AI-Powered File Organizer** is a Python-based file management system that automatically organizes files into user-defined folders using Generative AI.

Unlike traditional file organizers that depend entirely on fixed file extensions, this project uses **Google Gemini** to understand the context and purpose of a file from its filename and extension.

Users define their own categories, and the system creates and remembers those categories using JSON persistence. Files that cannot be confidently classified are collected and, with explicit user permission, can undergo deeper content-based AI analysis.

The project was developed incrementally from a basic Python file organizer into a more intelligent, configurable, and privacy-aware AI application.

---

## Problem Statement

Managing files manually becomes difficult when a directory contains different types of documents, assignments, presentations, spreadsheets, images, code files, and personal documents.

Traditional file organizers often rely on fixed rules such as:

```text
.docx → Word
.xlsx → Excel
.jpg  → Images
.pdf  → Documents
```

Although this approach works for obvious file types, it does not understand the **context or purpose** of a file.

For example:

```text
Python_Dictionaries.pptx
Electricity_bill.pdf
for_loops_Assignment.docx
```

have different purposes even though their extensions only describe their file formats.

The goal of this project was to create a system that allows users to define their own organizational structure while using AI to make more intelligent classification decisions.

---

## Tools & Technologies

### Programming Language

* **Python**

### Libraries

* `os` — file and directory handling
* `shutil` — moving files
* `json` — persistent category storage

### AI / API

* **Google Gemini API**
* **Google Gen AI Python SDK**

### Development Tools

* **Visual Studio Code**
* **PowerShell**
* **Git**
* **GitHub**

---

## Methods

### 1. User-Defined Categories

The user can define categories such as:

```text
Word, Excel, Personal, Finance, Projects
```

The system automatically creates the corresponding folders.

Duplicate categories are prevented.

---

### 2. Persistent Category Storage

Categories are stored in a JSON file:

```text
ai_categories.json
```

On the first run, the user defines the categories.

On subsequent runs, the existing categories are loaded automatically, with an option to add new categories.

---

### 3. File Scanning

The program scans the current directory and ignores:

* existing category folders
* the organizer's own Python file
* README
* JSON configuration
* Git configuration
* development/test files

This prevents the program from processing its own infrastructure.

---

### 4. AI-Based Classification

For each file, Gemini receives:

```text
File name
File extension
Available user-defined categories
```

The model is instructed to select exactly one category or return:

```text
Unknown
```

This allows the system to make context-aware classification decisions instead of relying entirely on hardcoded rules.

---

### 5. Unknown File Handling

Files that Gemini cannot confidently classify are collected instead of immediately interrupting the workflow.

After all files have been processed, the user receives a single prompt asking whether they want AI to perform deeper content analysis.

This prevents repetitive prompts when multiple files are unknown.

---

### 6. Optional Content Analysis

Content analysis requires explicit user permission.

Only extensions included in the project's safe-analysis list are allowed to undergo deeper analysis:

```python
safe_extensions = [".txt", ".md", ".csv", ".json", ".pptx", ".py"]
```

When permitted, the selected file is uploaded to Gemini and analyzed using its actual content.

The uploaded Gemini file is deleted after analysis when possible.

---

### 7. Error Handling

API requests are wrapped in exception handling so that failures such as:

* network errors
* API errors
* SSL problems
* failed uploads

do not automatically terminate the entire program.

Instead, the affected file is treated as unclassified and the organizer can continue.

---

### 8. File Safety

Before moving a file, the program checks whether a file with the same name already exists in the destination folder.

If a duplicate exists, the move is skipped rather than overwriting the existing file.

User-defined category names are also validated before being used as folder paths.

---

## Key Insights

### AI classification is more flexible than fixed extension rules

A file extension tells us what format a file uses, but not necessarily why the file exists.

For example:

```text
Electricity bill.pdf
```

and:

```text
Python Operators.pdf
```

are both PDF files but have completely different purposes.

Using filename context allows Gemini to make a more meaningful classification.

---

### User-defined categories make the system flexible

Instead of forcing every user to follow the same folder structure, the system adapts to the organizational structure chosen by the user.

For example, one user might choose:

```text
University
Projects
Finance
Personal
```

while another might choose:

```text
Clients
Bills
Work
Learning
```

The AI works with either structure.

---

### AI should not always receive file contents

Content-based AI analysis can provide deeper understanding, but it may also expose sensitive information to an external AI service.

For this reason, the system follows a two-stage approach:

```text
Filename + Extension
        ↓
AI Classification
        ↓
Unknown?
        ↓
Ask for permission
        ↓
Optional Content Analysis
```

This provides a balance between automation and privacy.

---

### Persistence improves usability

Saving categories in JSON means users do not have to recreate their folder structure every time the program runs.

This turns a simple script into a reusable application.

---


### Output

The program displays the classification and movement of files in the terminal.

Example:

```text
Python_Dictionaries.pptx ➡ Presentations
Students list.xlsx ➡ Excel
WhatsApp Image 2026...jpeg ➡ Personal
```

For uncertain files:

```text
AI could not find a suitable category for: unknown_file.xyz
```

If content analysis is permitted:

```text
1 files could not be classified
Do you want AI to analyze their content? (y/n)y

unknown_file.pdf ➡ Finance
```

---

## How to Run This Project

### 1. Clone the repository

```bash
git clone <your-github-repository-url>
```

### 2. Open the project folder

```bash
cd File-Organizer
```

### 3. Install the required package

```bash
pip install google-genai
```

### 4. Configure your Gemini API key

Set your Gemini API key as an environment variable:

```text
GEMINI_API_KEY
```

Do **not** hardcode the API key inside the Python source code.

### 5. Run the program

```bash
python file-organizer.py
```

### 6. Define categories

On the first run, enter categories separated by commas:

```text
University, Projects, Finance, Personal
```

The program creates the folders and stores the categories for future runs.

---

## Result & Conclusion

The project successfully evolved from a basic extension-based file organizer into a **user-configurable AI-powered file management system**.

The final implementation provides:

* User-defined categories
* Persistent category storage
* AI-based file classification
* Unknown-file handling
* Optional content-based analysis
* User permission before deeper AI analysis
* Duplicate-file protection
* Category validation
* API error handling
* Uploaded-file cleanup
* Git/GitHub version control

The project also provided practical experience in **Python automation, API integration, Generative AI, prompt engineering, JSON persistence, exception handling, file-system operations, privacy considerations, debugging, and iterative software development**.

More importantly, the project demonstrated that integrating AI into an application is not only about generating an AI response. Reliable AI applications also require thoughtful handling of **errors, privacy, user control, persistence, and real-world edge cases**.

---

## Future Work

Potential future improvements include:

* Support for more content-analysis file formats
* Better logging and activity reports
* Classification confidence scores
* A graphical user interface
* Configuration settings for AI behavior
* Local/offline AI processing for privacy-sensitive environments
* Automated testing
* Improved file preview and classification history

---

## Author & Contact

**Zara Khan**

Computer Science Student | Python Instructor | Generative AI Enthusiast

**GitHub:** [Your GitHub Profile](https://github.com/)
**LinkedIn:** [Your LinkedIn Profile](https://www.linkedin.com/)

---

## Project Status

**Status: Completed Working Prototype**

The current version successfully demonstrates the complete AI-powered file organization workflow with persistent categories, optional content analysis, and basic safety and reliability measures.
