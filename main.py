import speech_recognition as sr
import os
import pyttsx3
from time import time
import openai
import elevenlabs
query=""
context = "You are Jarvis, Arrush's human assistant. You are joyful and full of personality. Your answers should be limited to 1-2 short sentences."

engine = pyttsx3.init()
openai.api_key = "sk-ijklmnopqrstuvwxijklmnopqrstuvwxijklmnop"
elevenlabs_api_key= "sk_4845f1da8c9f62c9945f38d318bb7ac5ff9fc2f59e768fe1"


def say(text: str) -> None:
    engine.say(text)
    engine.runAndWait()


def log(log: str) -> None:
    print(log)
    with open("status.txt","w") as f:
        f.write(log)


def take_command() -> str:
    # Captures voice input from the user.
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        try:
            recognizer.adjust_for_ambient_noise(source, duration=1)  # Adjusts for background noise
            audio = recognizer.listen(source)
            print("Recognizing...")
            query = recognizer.recognize_google(audio, language="en-in")
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

"""
# Initialize TTS

chatStr = ""  # Global variable for chat history

def chat(query):
    //Handles conversation with OpenAI's GPT model.
    global chatStr
    openai.api_key = apikey
    try:
        # Use the new OpenAI library syntax
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are Jarvis, an AI assistant."},
                {"role": "user", "content": query}
            ]
        )
        reply = response.choices[0].message.content
        say(reply)
        chatStr += f"User: {query}\nJarvis: {reply}\n"
        print(reply)
        return reply
    except Exception as e:
        print(f"Error during AI response: {e}")
        say("I'm sorry, there was an error processing your request.")
        return ""
        
        query = take_command()
                if query:
                    if "exit" in query.lower():
                        say("Goodbye!")
                        break
                    elif not execute_command(query):  # Check for commands first
                        chat(query)  # If no command matches, handle via chat

"""
def request_gpt(prompt: query)-> query:
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user","content": f"{prompt}"}],
        )
        return response.choices[0].message.content
    except Exception as e:
        log(f"Error during GPT request: {e}")
        return "I'm sorry, I encountered an issue processing your request."


if __name__ == "__main__":
    print("Welcome to Jarvis AI!")
    say("Welcome to Jarvis AI! ,Arrush")
    while True:
        try:
            query=take_command()
            if not query:
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

            #Speaking Response
            log("Responding...")
            os.system("start audio/response.wav")
            say("audio/response.wav")
        except KeyboardInterrupt:
            print("\nExiting...")
            say("Goodbye!")
            break
