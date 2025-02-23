import requests
import webbrowser
import speech_recognition as sr
import pyttsx3

# Replace with your NewsAPI key
NEWS_API_KEY = 'c29d283b2af34ab08fbbb422d8b53c31'
NEWS_API_URL = 'https://newsapi.org/v2/top-headlines'

# Initialize text-to-speech engine
engine = pyttsx3.init()

def speak(text):
    """Convert text to speech."""
    print(f"Assistant: {text}")  # Print the text in the terminal
    engine.say(text)
    engine.runAndWait()

def listen():
    """Convert speech to text."""
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("\nListening... (Say something)")
        recognizer.adjust_for_ambient_noise(source, duration=1)  # Reduce background noise
        audio = recognizer.listen(source, timeout=5)  # Listen for 5 seconds
    try:
        print("Recognizing...")
        query = recognizer.recognize_google(audio, language="en-US")
        print(f"You said: {query}")
        return query.lower()
    except sr.UnknownValueError:
        speak("Sorry, I didn't catch that. Please try again.")
        return None
    except sr.RequestError:
        speak("Sorry, there was an issue with the speech recognition service.")
        return None
    except sr.WaitTimeoutError:
        speak("Sorry, I didn't hear anything. Please try again.")
        return None

def fetch_news():
    """Fetch top 5 news articles using NewsAPI."""
    params = {
        'apiKey': NEWS_API_KEY,
        'country': 'us',  # You can change the country code
        'pageSize': 5     # Fetch top 5 news articles
    }
    response = requests.get(NEWS_API_URL, params=params)
    if response.status_code == 200:
        return response.json()['articles']
    else:
        speak("Failed to fetch news.")
        return []

def display_news(news_articles):
    """Display news titles and sources using speech and in the terminal."""
    speak("Here are the top 5 news articles:")
    print("\nTop 5 News Articles:")
    for i, article in enumerate(news_articles, start=1):
        news_text = f"{i}. {article['title']} - from {article['source']['name']}"
        speak(news_text)  # Speak out loud
    speak("Please say the number of the news article you want to learn more about, or say 'exit' to quit.")

def open_news_source(news_articles, choice):
    """Open the selected news article's URL in a browser."""
    if 1 <= choice <= len(news_articles):
        speak(f"Opening news article {choice}.")
        webbrowser.open(news_articles[choice - 1]['url'])
    else:
        speak("Invalid choice. Please try again.")
def listen():
    try:
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            print("\nListening... (Say something)")
            recognizer.adjust_for_ambient_noise(source, duration=1)
            audio = recognizer.listen(source, timeout=5)
        print("Recognizing...")
        query = recognizer.recognize_google(audio, language="en-US")
        print(f"You said: {query}")
        return query.lower()
    except:
        print("Voice recognition failed. Please type your input:")
        return input("Your choice: ").strip().lower()
def main():
    """Main function to handle the news assistant."""
    speak("Welcome to the News Assistant. Fetching the latest news...")
    news_articles = fetch_news()
    if not news_articles:
        return

    display_news(news_articles)

    while True:
        speak("Please say your choice.")
        user_input = listen()
        if user_input is None:
            continue
        if 'exit' in user_input:
            speak("Goodbye!")
            break
        try:
            choice = int(user_input)
            open_news_source(news_articles, choice)
        except ValueError:
            speak("Please say a valid number or 'exit'.")

if __name__ == "__main__":
    main()