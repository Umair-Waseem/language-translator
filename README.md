# Language Translator (CustomTkinter)

![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![GitHub Stars](https://img.shields.io/github/stars/your-username/language-translator?style=social)

**Language Translator** is a **user-friendly desktop application** built with **Python** and **CustomTkinter**.  
It goes beyond basic translations by offering grammar suggestions, translation confidence scoring, and text-to-speech support.

---

## 📑 Table of Contents
1. [Features](#-features)
2. [Why Use It](#-why-use-it)
3. [Screenshots](#-screenshots)
4. [Requirements](#-requirements)
5. [Project Structure](#-project-structure)
6. [Installation](#-installation)
7. [Running the App](#-running-the-app)
8. [Usage Guide](#-usage-guide)
9. [Keyboard Shortcuts](#-keyboard-shortcuts)
10. [Customization](#-customization)
11. [Troubleshooting](#-troubleshooting)
12. [Privacy & License](#-privacy--license)
13. [Tested Versions](#-tested-versions)
14. [Contributing](#-contributing)
15. [Acknowledgments](#-acknowledgments)

---

## ✨ Features
- Detects the source language automatically using **Google Translate** and `langdetect`.
- Enhances single-word translations with **Noun Mode**.
- Provides translation confidence scoring via back-translation.
- Offers grammar suggestions through **LanguageTool** *(Java required)*.
- Supports Text-to-Speech (TTS) with **gTTS** and **pygame**.
- Allows switching between Light and Dark themes.
- Saves translation history with options to reuse or delete entries.

---

## 💡 Why Use It
This application is designed to do more than translate text:
- Enhance single-word translation accuracy with **Noun Mode**.
- Assess translation reliability with the **confidence score**.
- Improve writing with **grammar suggestions**.
- Listen to your translations with **TTS**.
- Quickly revisit translations through the **history feature**.

---

## 📸 Screenshots
*(Replace with actual screenshots before publishing)*

| Light Mode | Dark Mode |
|------------|-----------|
| ![Light Screenshot](screenshots/light.png) | ![Dark Screenshot](screenshots/dark.png) |

---

## ✅ Requirements
- **Python 3.10+**.
- Stable internet connection (for translation & TTS).
- **Java (JRE 8+)** for grammar checking.
- Tkinter (included with Windows/macOS; install manually on Linux).

#### Linux Tkinter installation:
```bash
sudo apt install python3-tk
📦 Project Structure
arduino
Copy
Edit
Language_Translator/
├─ main.py
├─ requirements.txt
├─ README.md
├─ .gitignore
└─ translator_app/
   ├─ __init__.py
   ├─ config.py
   ├─ language_support.py
   ├─ state.py
   └─ theme.py
File Roles:

main.py — Launches the application.

config.py — Application constants and settings.

theme.py — Manages Light/Dark theme styles.

language_support.py — Supported languages and mappings.

state.py — UI logic, events, and state management.

🚀 Installation
1. Clone the repository
bash
Copy
Edit
git clone https://github.com/your-username/language-translator.git
cd language-translator
2. Create a virtual environment (recommended)
Windows (PowerShell):

powershell
Copy
Edit
py -m venv .venv
.venv\Scripts\Activate.ps1
macOS / Linux:

bash
Copy
Edit
python3 -m venv .venv
source .venv/bin/activate
3. Install dependencies
bash
Copy
Edit
pip install --upgrade pip
pip install -r requirements.txt
4. Install Java (JRE 8+) for grammar checking
Windows:

Download from Java Download Page.

Install and restart your computer.

macOS:

Download the .dmg from Java Download Page.

Install following the prompts.

Linux (Debian/Ubuntu):

bash
Copy
Edit
sudo apt update
sudo apt install default-jre
java -version
▶️ Running the App
bash
Copy
Edit
python main.py
When launched, the app displays:

Language selectors.

Input and output text areas.

Buttons: Translate, Copy, History, and TTS.

A confidence score in the status bar.

🧭 Usage Guide
Enter text into the input box.

Select source and target languages, or choose Auto Detect.

(Optional) Enable Noun Mode for single-word translations.

Click Translate.

Review the translation, confidence score, and grammar suggestions.

Use Copy, TTS, or History as needed.

Toggle Light/Dark mode from the header.

⌨️ Keyboard Shortcuts
Action	Shortcut
Translate	Ctrl + T
Swap languages	Ctrl + S
Toggle theme	Ctrl + L
Open history	Ctrl + H
Toggle Noun Mode	Ctrl + N

⚙️ Customization
Edit translator_app/config.py to change:

Font styles and sizes.

Light/Dark color palettes.

Maximum translation length and timeout settings.

Language groupings and context phrases.

🛠 Troubleshooting
ModuleNotFoundError: translator_app → Ensure translator_app/__init__.py exists.

Grammar check not working → Install Java (JRE 8+) and restart the app.

No sound from TTS → Check internet connection and audio output.

Timeout or network errors → Shorten input text or check your network.

Permission errors → Ensure the app has permission to write to translation_history.json.

🔒 Privacy & License
Translations are stored locally in translation_history.json.

No personal data is collected.

Google APIs process text for translation and TTS.

Licensed under the MIT License — see the LICENSE file for details.

🧪 Tested Versions
Component	Version
Python	3.11
pygame	2.6.x
customtkinter	5.2.x
deep-translator	1.11.x
langdetect	1.0.x
language-tool-python	2.7.x
gTTS	2.5.x

🤝 Contributing
Contributions are welcome! Please:

Keep the UI simple and consistent.

Write clean, maintainable code.

Focus on stability and incremental improvements.

🙏 Acknowledgments
CustomTkinter — Modern and customizable Tkinter framework.

deep-translator — Python package for multiple translation APIs.

LanguageTool — Grammar and style checking tool.

gTTS — Google Text-to-Speech API for Python.

pygame — Python library for multimedia applications.