import speech_recognition as sr
import os
import pyttsx3
import webbrowser
from time import time
import openai
import elevenlabs
query = ""
context = "You are Jarvis, Arrush's human assistant. You are joyful and full of personality. Your answers should be limited to 1-2 short sentences."

engine = pyttsx3.init()
openai.api_key = "sk-ijklmnopqrstuvwxijklmnopqrstuvwxijklmnop"
elevenlabs_api_key = "sk_4845f1da8c9f62c9945f38d318bb7ac5ff9fc2f59e768fe1"


def say(text: str) -> None:
    engine.say(text)
    engine.runAndWait()


def log(log: str) -> None:
    print(log)
    with open("status.txt", "w") as f:
        f.write(log)


def take_command() -> str:
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        try:
            recognizer.adjust_for_ambient_noise(source, duration=1)
            audio = recognizer.listen(source)
            print("Recognizing...")
            query = recognizer.recognize_google(audio, language="en-in").lower()
            return query
        except sr.UnknownValueError:
            print("Sorry, I could not understand the audio.")
            return ""
        except sr.RequestError:
            print("Speech service is unavailable.")
            return ""
        except Exception as e:
            print(f"An error occurred: {e}")
            return ""


def request_gpt(prompt: str) -> str:
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": f"{prompt}"}],
        )
        return response.choices[0].message.content
    except Exception as e:
        log(f"Error during GPT request: {e}")
        return "I'm sorry, I encountered an issue processing your request."


def execute_command(query: str) -> bool:
    """
    Handles predefined commands like opening websites or performing actions.
    Returns True if a command was executed, False otherwise.
    """
    if "open youtube" in query:
        say("Opening YouTube, Arrush.")
        webbrowser.open("https://www.youtube.com")
        return True
    elif "open google" in query:
        say("Opening Google.")
        webbrowser.open("https://www.google.com")
        return True
    elif "open github" in query:
        say("Opening GitHub.")
        webbrowser.open("https://github.com")
        return True
    elif "open whatsapp" in query:
        say("Opening WhatsApp Web.")
        webbrowser.open("https://web.whatsapp.com")
        return True
    elif "open spotify" in query:
        say("Opening Spotify.")
        webbrowser.open("https://open.spotify.com")
        return True
    elif "exit" in query or "goodbye" in query:
        say("Goodbye, Arrush!")
        exit()
    else:
        return False


if __name__ == "__main__":
    print("Welcome to Jarvis AI!")
    say("Welcome to Jarvis AI! Arrush")
    while True:
        try:
            query = take_command()
            if not query:
                continue

            if execute_command(query):  # Check for predefined commands first
                continue

            # Get response from GPT-3
            current_time = time()
            context += f"\nArrush: {query}\nJarvis: "
            response = request_gpt(context)
            context += response
            gpt_time = time() - current_time
            log(f"Finished generating response in {gpt_time:.2f} seconds.")

            # Convert response to audio
            current_time = time()
            audio = elevenlabs.generate(
                text=response, voice="Adam", model="eleven_monolingual_v1"
            )
            elevenlabs.save(audio, "audio/response.wav")
            audio_time = time() - current_time
            log(f"Finished generating audio in {audio_time:.2f} seconds.")

            # Speaking Response
            log("Responding...")
            os.system("start audio/response.wav")
            say("audio/response.wav")

        except KeyboardInterrupt:
            print("\nExiting...")
            say("Goodbye!")
            break
