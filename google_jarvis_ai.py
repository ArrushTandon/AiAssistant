import speech_recognition as sr
import os
import pyttsx3
import google.generativeai as genai

# 1️⃣ SETUP GOOGLE GEMINI API KEY
GEMINI_API_KEY = "AIzaSyCrlz1nb67V6sVGi5Z-wTsSBiTyYm7viDo"
genai.configure(api_key=GEMINI_API_KEY)

# 2️⃣ SETUP TEXT-TO-SPEECH ENGINE
engine = pyttsx3.init()

def say(text: str):
    """Speaks the given text using pyttsx3."""
    print(f"Jarvis: {text}")  # Debugging
    engine.say(text)
    engine.runAndWait()

def take_command() -> str:
    """Captures voice input from the user."""
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        try:
            recognizer.adjust_for_ambient_noise(source, duration=1)
            audio = recognizer.listen(source)
            print("Recognizing...")
            query = recognizer.recognize_google(audio, language="en-in")
            return query
        except sr.UnknownValueError:
            print("Sorry, I couldn't understand.")
            return ""
        except sr.RequestError:
            print("Speech service unavailable.")
            return ""
        except Exception as e:
            print(f"An error occurred: {e}")
            return ""


USER_NAME = "Arrush"


def generate_response(prompt: str) -> str:
    """Generates a response using Google Gemini API with Jarvis personality."""
    try:
        model = genai.GenerativeModel("gemini-pro")
        system_prompt = (
            f"You are J.A.R.V.I.S, an advanced AI assistant modeled after the AI from Iron Man. "
            f"You must address the user as 'ARRUSH', maintaining a formal and efficient tone. "
            "You provide smart, witty, and informative responses while maintaining professionalism."
        )
        full_prompt = f"{system_prompt}\nUser: {prompt}\nJarvis:"

        response = model.generate_content(full_prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Error generating response: {e}")
        return f"I'm sorry, ARRUSH. I encountered an issue."


# MAIN LOOP
if __name__ == "__main__":
    print("Welcome to Jarvis AI!")
    say("Welcome to Jarvis AI!")

    while True:
        try:
            query = take_command()
            if not query:
                continue

            if "exit" in query.lower():
                say("Goodbye!")
                break

            # **Use Gemini API instead of GPT**
            response = generate_response(query)

            # Speak the response
            say(response)

        except KeyboardInterrupt:
            print("\nExiting...")
            say("Goodbye!")
            break
