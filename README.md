# Language Translator (CustomTkinter)

![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![GitHub Stars](https://img.shields.io/github/stars/your-username/language-translator?style=social)

A simple and friendly desktop application for translating text, with additional helpful features.  
Built with **Python** and **CustomTkinter**.

---

## ✨ Features
- Automatic language detection using **Google Translate** and `langdetect`
- **Noun Mode** for more accurate single-word translations
- Confidence score via back-translation
- Grammar hints with **LanguageTool** *(Java required)*
- **Text-to-Speech (TTS)** using `gTTS` and `pygame`
- Light/Dark mode toggle
- Translation history with reuse and delete options

> ℹ️ **Note:** Translation and TTS require an internet connection.

---

## 📸 Screenshots
*Replace these placeholders with real screenshots before publishing.*

| Light Mode | Dark Mode |
|------------|-----------|
| ![Light Screenshot](screenshots/light.png) | ![Dark Screenshot](screenshots/dark.png) |

---

## ✅ Requirements
- Python **3.10+**
- Internet connection
- Java (JRE 8+) for grammar checking
- Tkinter (included with Windows/macOS; on Linux install `python3-tk` if missing)

---

## 📂 Project Structure

```plaintext

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
File roles:

main.py — starts the application

config.py — stores constants, colors, and settings

theme.py — handles Light/Dark theme styles

language_support.py — manages supported languages and mappings

state.py — contains UI logic, events, and application state

🚀 Installation
1) Clone the repository
bash
Copy
Edit
git clone https://github.com/your-username/language-translator.git
cd language-translator
2) Create a virtual environment (recommended)
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
3) Install dependencies
bash
Copy
Edit
pip install --upgrade pip
pip install -r requirements.txt
4) Install Java for grammar checking
LanguageTool requires the Java Runtime Environment (JRE).

Windows:

Visit: Java Download Page

Download Windows Offline (64-bit)

Run the installer and follow the prompts

Restart your computer

Verify installation:

bash
Copy
Edit
java -version
macOS:

Visit: Java Download Page

Download the macOS installer

Open the .dmg file and follow the installation steps

Verify installation:

bash
Copy
Edit
java -version
Linux (Debian/Ubuntu):

bash
Copy
Edit
sudo apt-get update
sudo apt-get install -y default-jre
java -version
▶️ Running the App
bash
Copy
Edit
python main.py
When launched, the app will display:

Language selectors

Input and output text boxes

Buttons for Translate, Copy, History, and TTS

A status bar with the confidence score

🧭 How to Use
Type or paste text into the Input box

Select the source and target languages, or choose Auto Detect for the source

(Optional) Turn on Noun Mode for single-word translations

Click Translate

Review the translation, confidence score, and grammar hints

Use Copy, TTS, and History as needed

Toggle between Light and Dark mode from the header

⌨️ Shortcuts
Action	Shortcut
Translate	Ctrl + T
Swap languages	Ctrl + S
Toggle theme	Ctrl + L
Open history	Ctrl + H
Toggle Noun Mode	Ctrl + N

⚙️ Customization
Edit translator_app/config.py to modify:

Font sizes and styles

Light/Dark color palettes

Translation limits and timeouts

Language groupings and context phrases

🛠 Troubleshooting
ModuleNotFoundError: translator_app → Ensure translator_app/__init__.py exists

Grammar check not working → Install Java (JRE 8+) and restart the app

No sound from TTS → Check speakers and internet connection

Timeout or network errors → Use shorter text and ensure a stable connection

Permission errors → Ensure the app can write to translation_history.json

🔒 Privacy
Translations are stored locally in translation_history.json

No personal data is collected by the app

Google APIs process your text only temporarily for translation and TTS

📌 Tested Versions
Python 3.11

pygame 2.6.x

customtkinter 5.2.x

deep-translator 1.11.x

langdetect 1.0.x

language-tool-python 2.7.x

gTTS 2.5.x

🤝 Contributing
We welcome contributions! Please:

Keep the interface simple and consistent

Write clean, readable code

Focus on stability and incremental improvements

📄 License
MIT License — You may use and modify this project with proper credit.

🙏 Acknowledgments
CustomTkinter

deep-translator

LanguageTool

gTTS

pygame
