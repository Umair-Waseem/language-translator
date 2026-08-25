# Language Translator

A desktop application for translating text between languages, with automatic
language detection, a translation-confidence estimate, English grammar
suggestions, text-to-speech, and a translation history that can be browsed and
reused. It is built in Python with
[CustomTkinter](https://github.com/TomSchimansky/CustomTkinter)
for a modern, responsive interface.

Translation runs on a background thread, so the window stays responsive while a
request is in progress.

---

## Features

- **Automatic language detection.** The source language is detected with
  `langdetect`, supported by Unicode script heuristics for Chinese, Japanese,
  Korean, and Arabic.
- **Translation confidence.** The result is translated back into the source
  language and compared with the original to give an approximate quality score.
- **Noun mode.** For short inputs in a supported language pair, the word is
  placed in a brief contextual phrase to improve single-word translations.
  Other pairs are translated directly.
- **English grammar suggestions.** Powered by
  [LanguageTool](https://languagetool.org/); mistakes are underlined, and
  hovering over one shows the suggested correction.
- **Text-to-speech.** Both the source text and the translation can be read
  aloud.
- **Translation history.** Past translations are saved, and can be reused or
  deleted individually.
- **Light and dark themes.** The appearance can be switched at any time.

---

## Requirements

- **Python 3.9 or later.**
- **An internet connection.** Translation and text-to-speech rely on online
  services.
- **Java 17 or later** — only required for grammar checking. If Java is not
  installed, every other feature continues to work and grammar checking is
  simply skipped.
- **On Linux, the Tk toolkit** (`python3-tk`), which some distributions do not
  install with Python by default.

---

## Installation

**1. Clone the repository.**

```bash
git clone https://github.com/Umair-Waseem/language-translator
cd language-translator
```

**2. (Optional) Create and activate a virtual environment.**

```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS / Linux:
source venv/bin/activate
```

**3. Install the Python dependencies.**

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**4. (Optional) Install Java 17 or later for grammar checking.**

- **Windows and macOS:** download and install a current release from
  [adoptium.net](https://adoptium.net/) or [java.com](https://www.java.com/en/download/).
- **Linux (Debian/Ubuntu):**

  ```bash
  sudo apt update
  sudo apt install -y default-jre
  java -version
  ```

The first time grammar checking runs, LanguageTool downloads a language package
(roughly 250 MB), so the first check may take a moment. Later checks are fast.

**5. (Linux only) Install Tkinter if it is missing.**

```bash
sudo apt install -y python3-tk
```

---

## Running the Application

```bash
python main.py
```

The window provides source and target language selectors, an input box and a
read-only output box, and controls for translating, cancelling, copying,
clearing, playing audio, and opening the history.

A typical workflow:

1. Enter or paste text into the input box.
2. Choose the source and target languages, or leave the source on
   **Auto Detect**.
3. (Optional) Enable **Noun Mode** for a single word.
4. Click **Translate** (or press `Ctrl + T`). A translation in progress can be
   stopped with **Cancel**.
5. Review the translation, the confidence estimate, and any grammar
   suggestions.
6. Copy or listen to the result, or open the history to reuse an earlier
   translation.
7. Use the swap button (⇄) to reverse the language pair. When a translation is
   present, the two boxes also exchange their text so it can be translated back.

---

## Keyboard Shortcuts

| Action           | Shortcut   |
| ---------------- | ---------- |
| Translate        | `Ctrl + T` |
| Swap languages   | `Ctrl + S` |
| Toggle theme     | `Ctrl + L` |
| Open history     | `Ctrl + H` |
| Toggle noun mode | `Ctrl + N` |

---

## How It Works

- **Detection** combines `langdetect` with script-based heuristics. Text in a
  distinctive script (for example Japanese kana or Arabic) is identified
  immediately, while other text is classified by `langdetect`. Detected codes
  are normalized to the codes Google Translate expects.
- **Translation** uses `deep-translator` with the free Google Translate
  endpoint, which accepts inputs of up to 5,000 characters. A network timeout is
  enforced so a slow connection cannot make the application hang.
- **Confidence** is derived by translating the result back into the source
  language and measuring its similarity to the original text. A known source
  language is required, so the estimate is not available when the source cannot
  be determined (for example, very short auto-detected text).
- **Grammar checking** currently supports English. LanguageTool is started on
  first use and reused afterwards; if it cannot start, grammar checking is
  disabled for the session without affecting the rest of the application.
- **Text-to-speech** uses `gTTS` for synthesis and `pygame` for playback.
- **History** is stored in `translation_history.json` and keeps the 100 most
  recent entries.

---

## Project Structure

```text
language-translator/
├── main.py                 # Entry point
├── requirements.txt        # Python dependencies
├── README.md
├── LICENSE
├── .gitignore
├── tests/                  # Unit and integration tests
│   ├── test_logic.py
│   └── test_app.py
└── translator_app/
    ├── __init__.py
    ├── config.py           # Constants, limits, fonts, and colors
    ├── theme.py            # Light/dark color accessors
    ├── languages.py        # Language name/code maps and code normalization
    ├── detection.py        # Source-language detection (no UI)
    ├── translation.py      # Translation, back-translation, and confidence (no UI)
    ├── grammar.py          # LanguageTool wrapper that degrades gracefully
    ├── tts.py              # Text-to-speech synthesis and playback
    ├── history.py          # Loads, trims, and persists translation history
    ├── tooltip.py          # Hover tooltip for grammar suggestions
    ├── history_window.py   # The translation-history window
    └── app.py              # The main window that connects everything
```

The logic modules (`detection`, `translation`, `grammar`, `history`,
`languages`) contain no interface code, which keeps them straightforward to test
in isolation.

---

## Testing

The test suite uses Python's built-in `unittest`, so no additional packages are
required.

```bash
# Run every test
python -m unittest discover -s tests -v

# Run only the logic tests (no display or network needed)
python -m unittest tests.test_logic -v
```

`tests/test_logic.py` covers detection, code normalization, confidence scoring,
history storage, and grammar-result handling. `tests/test_app.py` drives the
window itself with the network, audio, and grammar dependencies replaced by test
doubles; these tests are skipped automatically when no display is available.

---

## Notes and Limitations

- Translation and text-to-speech require an internet connection.
- The list of available languages is retrieved when the application starts. If
  it cannot be retrieved, a small built-in set of common languages is used
  instead.
- Grammar checking is limited to English and requires Java 17 or later.
- Noun mode applies only when both the source and target languages are among
  English, Spanish, French, German, Italian, Russian, Japanese, Chinese, and
  Arabic. Any other pair is translated directly.
- The free Google Translate endpoint limits each translation to fewer than
  5,000 characters.

---

## Troubleshooting

| Problem | Suggested fix |
| ------- | ------------- |
| `ModuleNotFoundError: translator_app` | Run the application from the project's root directory. |
| Grammar suggestions never appear | Install Java 17 or later and restart the application; allow time for the first-run download. |
| No audio | Check the system volume and audio output, and confirm you are connected to the internet. |
| Translation is slow or times out | Check your connection, or try a shorter input. |
| History is not saved | Ensure the application can write to `translation_history.json` in its working directory. |
| Some history entries are missing | Damaged records, such as those left by manual editing, are skipped when the file is loaded. |

---

## Screenshots

**Light mode**

<img width="1920" height="1031" alt="Language Translator in light mode" src="https://github.com/user-attachments/assets/75ca1210-2bcb-489c-bdad-0c6b3a83690e" />

**Dark mode**

<img width="1920" height="1037" alt="Language Translator in dark mode" src="https://github.com/user-attachments/assets/4b81044e-cdfc-4564-b3b0-7f32bdabeb7a" />

---

## License

This project is released under the [MIT License](LICENSE).

---

## Acknowledgments

- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) — modern Tkinter widgets
- [deep-translator](https://pypi.org/project/deep-translator/) — translation
- [langdetect](https://pypi.org/project/langdetect/) — language detection
- [LanguageTool](https://languagetool.org/) — grammar checking
- [gTTS](https://pypi.org/project/gTTS/) — text-to-speech
- [pygame](https://www.pygame.org/) — audio playback

---

## Contact

For questions or suggestions, please open an issue on GitHub or contact
`umairwaseem5.4.2003@gmail.com`.
