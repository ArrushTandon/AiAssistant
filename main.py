import speech_recognition as sr
import os
import pyttsx3
import openai
from time import time
from elevenlabs.client import ElevenLabs

# Set API keys
OPENAI_API_KEY = "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"
ELEVENLABS_API_KEY = "sk_c3cf3c18abbdf27d87947f76722b224280dce22179b6e83b"

# Initialize OpenAI and ElevenLabs client
openai.api_key = OPENAI_API_KEY
client = ElevenLabs(api_key=ELEVENLABS_API_KEY)

# TTS engine for fallback
engine = pyttsx3.init()

# Context for conversation
context = "You are Jarvis, Arrush's human assistant. You are joyful and full of personality."


def say(text: str):
    """Use ElevenLabs for speech synthesis or fallback to pyttsx3."""
    try:
        # Stream the generated speech
        audio_stream = client.generate(
            text=text,
            voice="Brian",
            model="eleven_multilingual_v2",
            stream=True
        )

        # Play the audio directly
        with open("response.mp3", "wb") as f:
            for chunk in audio_stream:
                f.write(chunk)

        os.system("start response.mp3")  # Play the response (Windows)
    except Exception as e:
        print(f"Error with ElevenLabs TTS: {e}. Falling back to pyttsx3.")
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


def request_gpt(prompt: str) -> str:
    """Sends a query to GPT-3.5 and returns the response."""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error during GPT request: {e}")
        return "I'm sorry, I encountered an issue."


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

            # Get GPT-3 response
            context += f"\nArrush: {query}\nJarvis: "
            response = request_gpt(context)
            context += response

            # Speak the response
            print(f"Jarvis: {response}")
            say(response)

        except KeyboardInterrupt:
            print("\nExiting...")
            say("Goodbye!")
            break
