import subprocess
import webbrowser
import urllib.parse
import datetime
import os
import re
import sys

try:
    import speech_recognition as sr
except ImportError:  # pragma: no cover - optional dependency
    sr = None

try:
    import pyttsx3
except ImportError:  # pragma: no cover - optional dependency
    pyttsx3 = None


# ============================================================
#                         MAX
#              Universal Chrome Assistant
# ============================================================

APP_NAME = "MAX"


# ============================================================
# TEXT TO SPEECH
# ============================================================

engine = None
if pyttsx3 is not None:
    engine = pyttsx3.init()
    engine.setProperty("rate", 175)
    engine.setProperty("volume", 1.0)


def speak(text):
    print(f"MAX: {text}")
    if engine is not None:
        engine.say(text)
        engine.runAndWait()


# ============================================================
# FIND GOOGLE CHROME
# ============================================================

def get_chrome_path():

    possible_paths = [

        r"C:\Program Files\Google\Chrome\Application\chrome.exe",

        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",

        os.path.expandvars(
            r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"
        )
    ]

    for path in possible_paths:

        if os.path.exists(path):
            return path

    return None


# ============================================================
# OPEN CHROME
# ============================================================

def open_chrome(url=None):

    chrome = get_chrome_path()

    if chrome:

        if url:
            subprocess.Popen([chrome, url])
        else:
            subprocess.Popen([chrome])

    else:

        # Chrome not found:
        # Use Windows default browser

        if url:
            webbrowser.open(url)
        else:
            webbrowser.open("https://www.google.com")


# ============================================================
# CONVERT USER WEBSITE INTO URL
# ============================================================

def make_url(website):

    website = website.strip()

    # Remove unnecessary words
    website = re.sub(
        r"^(website|site)\s+",
        "",
        website,
        flags=re.IGNORECASE
    )

    # Already a complete URL
    if website.startswith("http://"):
        return website

    if website.startswith("https://"):
        return website

    # localhost
    if website.startswith("localhost"):
        return "http://" + website

    # IP address
    if re.match(
        r"^\d{1,3}(\.\d{1,3}){3}",
        website
    ):
        return "http://" + website

    # Domain
    if "." in website:

        return "https://" + website

    # If it isn't a domain, search Google
    return (
        "https://www.google.com/search?q="
        + urllib.parse.quote_plus(website)
    )


# ============================================================
# OPEN ANY WEBSITE
# ============================================================

def open_anything(target):

    target = target.strip()

    url = make_url(target)

    speak(f"Opening {target}")

    open_chrome(url)


# ============================================================
# GOOGLE SEARCH
# ============================================================

def google_search(query):

    query = query.strip()

    url = (
        "https://www.google.com/search?q="
        + urllib.parse.quote_plus(query)
    )

    speak(f"Searching Google for {query}")

    open_chrome(url)


# ============================================================
# YOUTUBE SEARCH
# ============================================================

def youtube_search(query):

    query = query.strip()

    url = (
        "https://www.youtube.com/results?search_query="
        + urllib.parse.quote_plus(query)
    )

    speak(f"Searching YouTube for {query}")

    open_chrome(url)


# ============================================================
# VOICE INPUT
# ============================================================

def listen():

    if sr is None:
        speak("Voice recognition is not available because the required dependency is missing.")
        return ""

    recognizer = sr.Recognizer()

    with sr.Microphone() as source:

        print("\n🎤 Listening...")

        recognizer.adjust_for_ambient_noise(
            source,
            duration=0.5
        )

        try:

            audio = recognizer.listen(
                source,
                timeout=5,
                phrase_time_limit=10
            )

        except sr.WaitTimeoutError:

            print("No voice detected.")
            return ""

    try:

        command = recognizer.recognize_google(audio)

        print(f"You: {command}")

        return command.lower()

    except sr.UnknownValueError:

        speak("I could not understand you.")

        return ""

    except sr.RequestError:

        speak("Voice recognition is unavailable.")

        return ""


# ============================================================
# COMMAND PROCESSOR
# ============================================================

def process_command(command):

    if not command:
        return True

    command = command.lower().strip()


    # --------------------------------------------------------
    # EXIT
    # --------------------------------------------------------

    if command in [
        "exit",
        "quit",
        "stop",
        "close max",
        "goodbye"
    ]:

        speak("Goodbye.")

        return False


    # --------------------------------------------------------
    # OPEN CHROME
    # --------------------------------------------------------

    if command in [
        "open chrome",
        "start chrome",
        "launch chrome"
    ]:

        speak("Opening Chrome.")

        open_chrome()

        return True


    # --------------------------------------------------------
    # GOOGLE SEARCH
    # --------------------------------------------------------

    google_commands = [
        "search google for ",
        "search google ",
        "google search ",
        "search for ",
        "search "
    ]

    for prefix in google_commands:

        if command.startswith(prefix):

            query = command[len(prefix):].strip()

            if query:

                google_search(query)

            return True


    # --------------------------------------------------------
    # YOUTUBE SEARCH
    # --------------------------------------------------------

    youtube_commands = [
        "search youtube for ",
        "search youtube ",
        "youtube search "
    ]

    for prefix in youtube_commands:

        if command.startswith(prefix):

            query = command[len(prefix):].strip()

            if query:

                youtube_search(query)

            return True


    # --------------------------------------------------------
    # OPEN COMMAND
    #
    # Examples:
    #
    # open amazon.com
    # open wikipedia.org
    # open https://example.com
    # open mywebsite.com
    # open localhost:3000
    #
    # --------------------------------------------------------

    if command.startswith("open "):

        target = command[5:].strip()

        if target:

            # Special case
            if target == "chrome":

                open_chrome()

            else:

                open_anything(target)

            return True


    # --------------------------------------------------------
    # GO TO COMMAND
    #
    # Examples:
    #
    # go to amazon.com
    # go to wikipedia.org
    # go to google.com
    #
    # --------------------------------------------------------

    if command.startswith("go to "):

        target = command[6:].strip()

        if target:

            open_anything(target)

        return True


    # --------------------------------------------------------
    # VISIT COMMAND
    # --------------------------------------------------------

    if command.startswith("visit "):

        target = command[6:].strip()

        if target:

            open_anything(target)

        return True


    # --------------------------------------------------------
    # OPEN WEBSITE COMMAND
    # --------------------------------------------------------

    if command.startswith("open website "):

        target = command[13:].strip()

        if target:

            open_anything(target)

        return True


    # --------------------------------------------------------
    # OPEN SITE COMMAND
    # --------------------------------------------------------

    if command.startswith("open site "):

        target = command[10:].strip()

        if target:

            open_anything(target)

        return True


    # --------------------------------------------------------
    # TIME
    # --------------------------------------------------------

    if "what time" in command or command == "time":

        current_time = datetime.datetime.now().strftime(
            "%I:%M %p"
        )

        speak(f"The time is {current_time}")

        return True


    # --------------------------------------------------------
    # HELP
    # --------------------------------------------------------

    if command == "help":

        print("""
============================================================
                         MAX
============================================================

Examples:

open chrome

open google.com

open amazon.in

open wikipedia.org

open https://example.com

go to youtube.com

visit github.com

search Google for Python

search YouTube for Python tutorials

what time is it

exit

============================================================
""")

        speak("I can open any website you give me.")

        return True


    # --------------------------------------------------------
    # UNKNOWN COMMAND
    # --------------------------------------------------------

    speak(
        "I don't recognize that command. "
        "You can say open followed by any website."
    )

    return True


# ============================================================
# TEXT MODE
# ============================================================

def text_mode():

    print("""
============================================================
                       MAX TEXT MODE
============================================================

You can type:

open amazon.com
open wikipedia.org
open google.com
open anywebsite.com

or:

search Google for Python
search YouTube for music

Type exit to stop MAX.

============================================================
""")

    while True:

        command = input("\nYou: ")

        if not process_command(command):

            break


# ============================================================
# VOICE MODE
# ============================================================

def voice_mode():

    speak("MAX voice mode activated.")

    while True:

        command = listen()

        if command:

            if not process_command(command):

                break


# ============================================================
# MAIN MENU
# ============================================================

def main():

    print("""
============================================================
                         MAX
                  AI DESKTOP ASSISTANT
============================================================

1. Text Mode
2. Voice Mode
3. Exit

============================================================
""")

    while True:

        choice = input("Select: ").strip()

        if choice == "1":

            text_mode()

        elif choice == "2":

            voice_mode()

        elif choice == "3":

            speak("Goodbye.")

            sys.exit()

        else:

            print("Please enter 1, 2, or 3.")


# ============================================================
# START MAX
# ============================================================

if __name__ == "__main__":

    main()
