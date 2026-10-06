import webbrowser
import subprocess
import os
import urllib.parse
import urllib.request
import urllib.error
import datetime
import sys
import re
import ctypes
import time

try:
    import speech_recognition as sr
except ImportError:  # pragma: no cover - optional dependency
    sr = None

try:
    import pyttsx3
except ImportError:  # pragma: no cover - optional dependency
    pyttsx3 = None

# ============================================================
# MAX - Voice + Text Desktop Assistant
# ============================================================

APP_NAME = "MAX"
CURRENT_SITE = None

# -----------------------------
# Text-to-Speech
# -----------------------------

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


# -----------------------------
# Open Google Chrome
# -----------------------------

def open_chrome(url=None):
    chrome_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(
            r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"
        )
    ]

    chrome = None

    for path in chrome_paths:
        if os.path.exists(path):
            chrome = path
            break

    if chrome:
        if url:
            subprocess.Popen([chrome, url])
        else:
            subprocess.Popen([chrome])
    else:
        # Fallback to default browser
        if url:
            webbrowser.open(url)
        else:
            webbrowser.open("https://www.google.com")


# -----------------------------
# Voice Recognition
# -----------------------------

def listen():
    if sr is None:
        speak("Voice recognition is not available because the required dependency is missing.")
        return ""

    recognizer = sr.Recognizer()

    with sr.Microphone() as source:
        print("\nListening...")
        recognizer.adjust_for_ambient_noise(source, duration=0.5)

        try:
            audio = recognizer.listen(
                source,
                timeout=5,
                phrase_time_limit=8
            )
        except sr.WaitTimeoutError:
            print("No voice detected.")
            return ""

    try:
        command = recognizer.recognize_google(audio)
        print(f"You: {command}")
        return command.lower()

    except sr.UnknownValueError:
        speak("Sorry, I could not understand that.")
        return ""

    except sr.RequestError:
        speak("Voice recognition is currently unavailable.")
        return ""


# -----------------------------
# Open websites
# -----------------------------

def set_current_site(site_name):
    global CURRENT_SITE
    if site_name:
        CURRENT_SITE = site_name.lower().strip()


def open_website(site):
    global CURRENT_SITE

    websites = {
        "google": "https://www.google.com",
        "youtube": "https://www.youtube.com",
        "gmail": "https://mail.google.com",
        "github": "https://github.com",
        "facebook": "https://www.facebook.com",
        "instagram": "https://www.instagram.com",
        "whatsapp": "https://web.whatsapp.com",
        "linkedin": "https://www.linkedin.com",
        "chatgpt": "https://chatgpt.com",
        "stackoverflow": "https://stackoverflow.com"
    }

    site = site.lower().strip()

    if site in websites:
        CURRENT_SITE = site
        open_chrome(websites[site])
        speak(f"Opening {site}")
        return True

    # If user gives a full URL
    if site.startswith("http://") or site.startswith("https://"):
        CURRENT_SITE = "custom website"
        open_chrome(site)
        speak("Opening the website.")
        return True

    return False


# -----------------------------
# Google Search
# -----------------------------

def clean_search_query(query):
    query = (query or "").strip()
    if not query:
        return ""

    filler_words = {
        "this", "that", "the", "a", "an", "please", "now",
        "video", "videos", "song", "songs", "music"
    }

    parts = query.split()
    while parts and parts[0].lower() in filler_words:
        parts.pop(0)

    return " ".join(parts).strip()


def google_search(query):
    query = clean_search_query(query)
    if not query:
        query = "latest news"

    encoded = urllib.parse.quote_plus(query)

    url = f"https://www.google.com/search?q={encoded}"

    open_chrome(url)

    speak(f"Searching Google for {query}")


def chatgpt_prompt(prompt):
    prompt = (prompt or "").strip()
    if not prompt:
        speak("Please tell me what you want to ask ChatGPT.")
        return

    url = "https://chatgpt.com/?q=" + urllib.parse.quote_plus(prompt)
    open_chrome(url)
    if submit_chatgpt_prompt():
        speak("Sent your question to ChatGPT.")
    else:
        speak(
            "I opened ChatGPT with your question, but could not submit it. "
            "Make sure Chrome is open and try again."
        )


def submit_chatgpt_prompt():
    user32 = getattr(ctypes, "windll", None)
    enum_windows_proc_type = getattr(ctypes, "WINFUNCTYPE", None)
    if user32 is None or enum_windows_proc_type is None:
        print("Automatic ChatGPT submission requires Windows.")
        return False

    time.sleep(7)
    user32 = user32.user32
    chrome_windows = []
    enum_windows_proc = enum_windows_proc_type(
        ctypes.c_bool,
        ctypes.c_void_p,
        ctypes.c_void_p
    )

    def collect_chrome_window(hwnd, _):
        if not user32.IsWindowVisible(hwnd):
            return True

        title_length = user32.GetWindowTextLengthW(hwnd)
        title = ctypes.create_unicode_buffer(title_length + 1)
        user32.GetWindowTextW(hwnd, title, len(title))
        chrome_windows.append((hwnd, title.value.lower()))
        return True

    callback = enum_windows_proc(collect_chrome_window)
    user32.EnumWindows(callback, 0)

    chatgpt_window = next(
        (hwnd for hwnd, title in chrome_windows if "chatgpt" in title),
        None
    )
    foreground_window = user32.GetForegroundWindow()
    foreground_is_chrome = any(
        hwnd == foreground_window and "chrome" in title
        for hwnd, title in chrome_windows
    )
    hwnd = chatgpt_window or (
        foreground_window if foreground_is_chrome else None
    )

    if hwnd is None:
        print("Could not find an open Chrome window to submit the ChatGPT prompt.")
        return False

    user32.ShowWindow(hwnd, 9)
    user32.BringWindowToTop(hwnd)
    user32.SetForegroundWindow(hwnd)
    time.sleep(0.5)

    if user32.GetForegroundWindow() != hwnd:
        print("Windows did not allow MAX to focus the Chrome window.")
        return False

    user32.keybd_event(0x0D, 0, 0, 0)
    user32.keybd_event(0x0D, 0, 0x0002, 0)
    return True


# -----------------------------
# YouTube Search
# -----------------------------

def youtube_search(query):
    query = clean_search_query(query)
    if not query:
        query = "popular songs"

    encoded = urllib.parse.quote_plus(query)

    url = f"https://www.youtube.com/results?search_query={encoded}"

    open_chrome(url)

    speak(f"Searching YouTube for {query}")


def youtube_play(query):
    query = (query or "").strip()
    generic_requests = {
        "song", "songs", "music", "a song", "the song", "this song",
        "some songs", "some music", "video", "videos", "a video",
        "the video", "this video"
    }
    if query.lower() in generic_requests:
        query = "popular songs"
    elif query.lower().startswith(("the song ", "a song ", "this song ")):
        query = query.split(" ", 2)[-1].strip()
    elif query.lower().startswith(("the video ", "a video ", "this video ")):
        query = query.split(" ", 2)[-1].strip()

    if not query:
        query = "popular songs"

    search_url = (
        "https://www.youtube.com/results?search_query="
        + urllib.parse.quote_plus(query)
    )
    request = urllib.request.Request(
        search_url,
        headers={"User-Agent": "Mozilla/5.0"}
    )

    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            page = response.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, TimeoutError) as error:
        print(f"Could not resolve a YouTube video: {error}")
        open_chrome(search_url)
        speak(f"I couldn't start playback automatically. Showing YouTube results for {query}.")
        return

    match = re.search(
        r'"videoId"\s*:\s*"([A-Za-z0-9_-]{11})"',
        page
    )
    if match is None:
        open_chrome(search_url)
        speak(f"I couldn't find a playable video automatically. Showing YouTube results for {query}.")
        return

    video_url = (
        "https://www.youtube.com/watch?v="
        + match.group(1)
        + "&autoplay=1"
    )
    open_chrome(video_url)
    speak(f"Playing the top YouTube result for {query}")


# -----------------------------
# Command Processor
# -----------------------------

def process_command(command):
    global CURRENT_SITE

    if not command:
        return True

    command = command.lower().strip()

    # -------------------------
    # Context-aware follow-up commands
    # -------------------------

    if CURRENT_SITE == "chatgpt" and command not in {
        "exit", "quit", "stop", "close max", "goodbye", "shutdown",
        "help", "what can you do"
    }:
        chatgpt_prefixes = (
            "search chatgpt for ",
            "ask chatgpt ",
            "search for ",
            "search ",
            "ask ",
        )
        for prefix in chatgpt_prefixes:
            if command.startswith(prefix):
                prompt = command[len(prefix):].strip()
                if prompt:
                    chatgpt_prompt(prompt)
                return True

        if command.startswith(("what is ", "who is ", "why ", "how ", "explain ")):
            chatgpt_prompt(command)
            return True

    if CURRENT_SITE == "youtube":
        if command.startswith("play "):
            query = command[5:].strip()
            if query:
                youtube_play(query)
                return True

        if command.startswith("search "):
            query = command[7:].strip()
            if query:
                youtube_search(query)
                return True

        if command.startswith("watch "):
            query = command[6:].strip()
            if query:
                youtube_search(query)
                return True

    if CURRENT_SITE == "google":
        if command.startswith("search ") or command.startswith("google "):
            query = command[7:].strip() if command.startswith("search ") else command[6:].strip()
            if query:
                google_search(query)
                return True

    # -------------------------
    # Exit
    # -------------------------

    if command in [
        "exit",
        "quit",
        "stop",
        "close max",
        "goodbye",
        "shutdown"
    ]:
        CURRENT_SITE = None
        speak("Goodbye.")
        return False

    # -------------------------
    # Help
    # -------------------------

    if command in ["help", "what can you do"]:
        speak(
            "I can open Chrome, search Google, search YouTube, "
            "open websites, tell the time, and perform basic commands."
        )
        return True

    # -------------------------
    # Time
    # -------------------------

    if "time" in command:
        current_time = datetime.datetime.now().strftime("%I:%M %p")
        speak(f"The time is {current_time}")
        return True

    # -------------------------
    # Open Chrome
    # -------------------------

    if command in [
        "open chrome",
        "start chrome",
        "launch chrome"
    ]:
        CURRENT_SITE = "chrome"
        speak("Opening Chrome.")
        open_chrome()
        return True

    # -------------------------
    # Open websites
    # -------------------------

    if command.startswith("open "):

        website = command[5:].strip()

        if open_website(website):
            return True

        # Example:
        # "open python.org"

        if "." in website:
            if not website.startswith("http"):
                website = "https://" + website

            CURRENT_SITE = "custom website"
            open_chrome(website)
            speak("Opening the website.")
            return True

    # -------------------------
    # Google Search
    # -------------------------

    search_prefixes = [
        "search google for ",
        "google search ",
        "search for ",
        "search "
    ]

    for prefix in search_prefixes:

        if command.startswith(prefix):

            query = command[len(prefix):].strip()

            if query:
                google_search(query)

            return True

    # -------------------------
    # YouTube
    # -------------------------

    youtube_prefixes = [
        "search youtube for ",
        "youtube search ",
        "play "
    ]

    for prefix in youtube_prefixes:

        if command.startswith(prefix):

            query = command[len(prefix):].strip()

            if query:
                if prefix == "play ":
                    youtube_play(query)
                else:
                    youtube_search(query)

            return True

    if command.startswith("watch "):
        query = command[6:].strip()
        if query:
            youtube_play(query)
        return True

    # -------------------------
    # Direct YouTube opening
    # -------------------------

    if "open youtube" in command:

        CURRENT_SITE = "youtube"
        open_chrome("https://www.youtube.com")
        speak("Opening YouTube. Tell me what to play next.")
        return True

    # -------------------------
    # Google
    # -------------------------

    if "open google" in command:

        CURRENT_SITE = "google"
        open_chrome("https://www.google.com")
        speak("Opening Google. Tell me what to search next.")
        return True

    # -------------------------
    # Unknown command
    # -------------------------

    speak(
        "I don't know that command yet. "
        "Try saying search Google for something."
    )

    return True


# -----------------------------
# Text Mode
# -----------------------------

def text_mode():

    print("\n==============================")
    print("        MAX TEXT MODE")
    print("==============================")
    print("Type 'help' for commands.")
    print("Type 'exit' to close MAX.")

    while True:

        command = input("\nYou: ")

        if not process_command(command):
            break


# -----------------------------
# Voice Mode
# -----------------------------

def voice_mode():

    speak("MAX voice mode activated.")

    while True:

        command = listen()

        if command:

            if not process_command(command):
                break


# -----------------------------
# Main Program
# -----------------------------

def main():

    print("\n================================")
    print("          MAX ASSISTANT")
    print("================================")
    print("1. Text mode")
    print("2. Voice mode")
    print("3. Exit")

    while True:

        choice = input("\nSelect mode: ").strip()

        if choice == "1":
            text_mode()

        elif choice == "2":
            voice_mode()

        elif choice == "3":
            speak("Goodbye.")
            sys.exit()

        else:
            print("Please select 1, 2, or 3.")


if __name__ == "__main__":
    main()
