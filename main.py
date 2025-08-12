# main.py
# Entry point for the modularized app.

from translator_app.state import app, initialize_application

if __name__ == "__main__":
    initialize_application()
    app.mainloop()
