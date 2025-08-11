import pyttsx3
import threading

def speak(text):
    """Convert text to speech using pyttsx3"""
    engine = pyttsx3.init()  # Initialize text-to-speech engine
    voices = engine.getProperty('voices')  # Get available voices
    for voice in voices:
        if "female" in voice.name.lower() or "zira" in voice.name.lower():  # Prefer female voice
            engine.setProperty('voice', voice.id)  # Set preferred voice
            break
    engine.say(text)  # Queue text for speech
    engine.runAndWait()  # Wait for speech to complete

def speak_async(text):
    """Convert text to speech asynchronously"""
    threading.Thread(target=speak, args=(text,)).start()  # Start speech in background thread 