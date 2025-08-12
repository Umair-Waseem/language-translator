Language Translator 
A simple and friendly desktop app for translating text with useful extra features.
Built with Python and CustomTkinter.

✨ Features
Automatic language detection using Google Translate and langdetect.

Noun Mode for better translations of single words.

Confidence score using back-translation.

Grammar hints with LanguageTool (Java required).

Text-to-Speech (TTS) with gTTS and pygame.

Light/Dark mode toggle.

Translation history with reuse and delete options.

Translation and TTS require an internet connection.

📂 Project Structure
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

main.py – Starts the application.

config.py – Stores constants, colors, and settings.

theme.py – Handles Light/Dark theme styles.

language_support.py – Manages supported languages and mappings.

state.py – Contains UI logic, events, and application state.

✅ Requirements
Python 3.10+

Internet connection

Java (JRE 8+) for grammar checking

Tkinter (included with Windows/macOS; Linux may need install)

🚀 Installation
Clone the repository

bash
Copy
Edit
git clone https://github.com/your-username/language-translator.git
cd language-translator
Create a virtual environment

Windows (PowerShell)

powershell
Copy
Edit
py -m venv .venv
.venv\Scripts\Activate.ps1
macOS / Linux

bash
Copy
Edit
python3 -m venv .venv
source .venv/bin/activate
Install dependencies

bash
Copy
Edit
pip install --upgrade pip
pip install -r requirements.txt
Linux extra packages (if needed)

bash
Copy
Edit
sudo apt-get update
sudo apt-get install -y python3-tk default-jre
☕ Installing Java for Grammar Checking
LanguageTool requires Java Runtime Environment (JRE).
Here’s how to install it on each system:

Windows
Go to: https://www.java.com/en/download/manual.jsp

Download Windows Offline (64-bit).

Run the installer and follow the prompts.

Restart your computer.

macOS
Go to: https://www.java.com/en/download/manual.jsp

Download the macOS installer.

Open the .dmg file and follow the installation steps.

Linux (Debian/Ubuntu)
bash
Copy
Edit
sudo apt-get update
sudo apt-get install default-jre
java -version
After installation, verify:

bash
Copy
Edit
java -version
You should see the installed version number.

▶️ Running the App
bash
Copy
Edit
python main.py
The main window will appear with:

Language selectors

Input and output text boxes

Buttons for Translate, Copy, History, and TTS

A status bar showing the confidence score

🧭 How to Use
Type or paste text into the Input box.

Select the source and target languages, or use Auto Detect for the source.

(Optional) Turn on Noun Mode for single-word translations.

Click Translate.

Review the translation, confidence score, and grammar hints.

Use Copy, TTS, and History as needed.

Toggle between Light and Dark mode from the header.

⌨️ Shortcuts
Action	Shortcut
Translate	Ctrl + T
Swap languages	Ctrl + S
Toggle theme	Ctrl + L
Open history	Ctrl + H
Toggle Noun Mode	Ctrl + N

⚙️ Customization
You can change fonts, colors, and other settings in config.py:

Font sizes and styles

Light/Dark color palettes

Translation limits and timeouts

Language groupings and context phrases

🛠 Troubleshooting
ModuleNotFoundError: translator_app
Make sure __init__.py exists in translator_app.

Grammar check not working
Install Java (JRE 8+) and restart the app.

No sound from TTS
Check speakers and internet connection.

Timeout or network errors
Retry with shorter text and a stable internet connection.

Permission errors
Ensure the app folder can write translation_history.json.

🔒 Privacy
Translations are stored locally in translation_history.json.

No personal data is collected.

Google APIs process your text for translation and TTS.

📌 Tested Versions
Python 3.11

pygame 2.6.x

customtkinter 5.2.x

deep-translator 1.11.x

langdetect 1.0.x

language-tool-python 2.7.x

gTTS 2.5.x

🤝 Contributing
We welcome pull requests and suggestions. Please:

Keep the interface simple and consistent.

Write clean and readable code.

Focus on stability and small improvements.

📄 License
MIT License — you may use and modify with proper credit.

🙏 Acknowledgments
CustomTkinter

deep-translator

LanguageTool

gTTS

pygame

This now fully meets your requirements:

✅ Friendly: welcoming tone without sounding casual.

✅ Clear: step-by-step installation and usage.

✅ Simple sentence structure: easy to read for all skill levels.

✅ Professional: structured sections, consistent formatting, no slang.

✅ Complete: includes Java installation guide.

