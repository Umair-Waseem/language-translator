# 🈯 Language Translator

A simple, friendly desktop application for translating text, checking grammar, listening to translations with Text-to-Speech (TTS), and keeping a translation history — all in one place. Built with Python and CustomTkinter for a modern, lightweight interface.

---

## 🚀 Key Features

* 🌐 **Automatic Language Detection** — Uses Google Translate and `langdetect`.
* 📝 **Noun Mode** — Improves accuracy for single-word translations.
* 📊 **Confidence Score** — Shows translation quality through back-translation.
* 🧠 **Grammar Hints** — Provided by LanguageTool ([Java required](https://www.java.com/en/download/)).
* 🔊 **Text-to-Speech (TTS)** — Listen to translations instantly.
* 🎨 **Light/Dark Mode** — Switch themes easily.
* 📜 **Translation History** — Save, reuse, or delete past translations.

---

## 💼 Best For

* Learning new languages.
* Quick translation of documents or messages.
* Enhancing writing with grammar suggestions.
* Keeping a personal vocabulary log.
* Translating multilingual communications.

---

## ⚙️ Getting Started

> **Requires Python 3.10 or later**

### 1. Download the Project

```bash
git clone https://github.com/Umair-Waseem/language-translator
cd language-translator
```

### 2. (Optional) Create a Virtual Environment

```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Requirements

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Install Java (JRE 8+) for Grammar Checking

**Windows**

1. [Download Java](https://www.java.com/en/download/)
2. Install Java and restart your computer.

**macOS**

1. [Download Java installer](https://www.java.com/en/download/)
2. Install Java.

**Linux (Debian/Ubuntu)**

```bash
sudo apt update
sudo apt install -y default-jre
java -version
```

### 5. (Linux only) Install Tkinter if Missing

```bash
sudo apt install -y python3-tk
```

---

## ▶️ Run the App

```bash
python main.py
```

When launched, the app will display:

* Language selectors.
* Input and output text boxes.
* Buttons for Translate, Copy, History, and TTS.
* A status bar with the confidence score.

---

## 📁 Project Structure

```bash
Language_Translator/
├── main.py
├── requirements.txt
├── README.md
├── .gitignore
└── translator_app/
    ├── __init__.py
    ├── config.py
    ├── language_support.py
    ├── state.py
    └── theme.py
```

**File Roles**

* `main.py` — Runs the application.
* `config.py` — Stores constants and settings.
* `theme.py` — Manages Light/Dark themes.
* `language_support.py` — Handles language mappings.
* `state.py` — Manages UI logic and events.

---

## 🧩 Supported Features

| Feature             | Description                                |
| ------------------- | ------------------------------------------ |
| Automatic Detection | Detects source language automatically.     |
| Noun Mode           | Improves single-word translation accuracy. |
| Grammar Checking    | Requires Java (JRE 8+).                    |
| Confidence Score    | Shows translation quality.                 |
| Text-to-Speech      | Plays translated text aloud.               |
| Translation History | Saves and reuses translations.             |

---

## 🖥️ How It Works

1. Enter or paste text into the input box.
2. Select source and target languages, or choose **Auto Detect**.
3. (Optional) Turn on **Noun Mode** for single words.
4. Click **Translate**.
5. Review the translation, confidence score, and grammar hints.
6. Use **Copy**, **TTS**, or **History**.
7. Switch between Light and Dark mode as needed.

---

## ⌨️ Keyboard Shortcuts

| Action           | Shortcut |
| ---------------- | -------- |
| Translate        | Ctrl + T |
| Swap languages   | Ctrl + S |
| Toggle theme     | Ctrl + L |
| Open history     | Ctrl + H |
| Toggle Noun Mode | Ctrl + N |

---

## 📦 Required Libraries

Install all libraries with:

```bash
pip install -r requirements.txt
```

Main packages:

* `customtkinter`
* `deep-translator`
* `langdetect`
* `language-tool-python`
* `gTTS`
* `pygame`

---

## 🪪 License

Licensed under the **MIT License**

---

## 🙏 Acknowledgments

* [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) — Modern Tkinter styling.
* [deep-translator](https://pypi.org/project/deep-translator/) — Translation API.
* [LanguageTool](https://languagetool.org/) — Grammar checking.
* [gTTS](https://pypi.org/project/gTTS/) — Text-to-Speech.
* [pygame](https://www.pygame.org/) — Audio playback.

---

## ❓ Troubleshooting

* **`ModuleNotFoundError: translator_app`** → Check `translator_app/__init__.py` exists.
* **Grammar check not working** → Install Java and restart.
* **No TTS sound** → Check speakers and internet.
* **Network/timeout errors** → Try shorter text or check your connection.
* **Permission errors** → Allow write access to `translation_history.json`.

---

## 🖼️ Screenshots

**Light Mode:**

<img width="1920" height="1031" alt="image" src="https://github.com/user-attachments/assets/47abafee-591a-46e9-accc-c63b49bba061" />

---

**Dark Mode:**

<img width="1920" height="1037" alt="1231231212412412" src="https://github.com/user-attachments/assets/1935b0ea-ee3b-4603-aae4-78703f7fd21a" />

---

## 📬 Contact

Questions or suggestions?

* Open an issue on GitHub.
* Email: `umairwaseem5.4.2003@gmail.com`

> Made with ❤️ using Python — helping you translate smarter, faster, and easier.
