import speech_recognition as sr
import pyttsx3
import google.generativeai as genai
import requests  # For making HTTP requests to external APIs
from datetime import datetime  # For timestamping news articles
from computer_vision import ComputerVisionModule  # Import the vision module

class Chatbot:
    def __init__(self, api_key: str, user_name: str = "Sir", weather_api_key: str = None, news_api_key: str = None, stock_api_key: str = None,stable_diffusion_model_id: str = "runwayml/stable-diffusion-v1-5"):
        self.api_key = api_key  # Google Gemini API key
        self.user_name = user_name
        self.weather_api_key = weather_api_key  # OpenWeatherMap API key
        self.news_api_key = news_api_key  # NewsAPI key
        self.stock_api_key = stock_api_key  # Alpha Vantage API key
        self.engine = pyttsx3.init()
        self.setup_gemini()
        self.vision_module = ComputerVisionModule(stable_diffusion_model_id)

    def setup_gemini(self):
        """Configures the Google Gemini API."""
        genai.configure(api_key=self.api_key)

    def say(self, text: str):
        """Speaks the given text using pyttsx3."""
        print(f"Jarvis: {text}")  # Debugging
        self.engine.say(text)
        self.engine.runAndWait()

    def take_command(self) -> str:
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

    def generate_response(self, prompt: str) -> str:
        """Generates a response using Google Gemini API or fetches real-time data."""
        try:
            # Check for specific real-time data requests
            if "temperature" in prompt.lower():
                return self.get_current_temperature()
            elif "news" in prompt.lower():
                return self.get_latest_news()
            elif "stock price" in prompt.lower():
                return self.get_stock_price()
            else:
                # Use Gemini for general queries
                model = genai.GenerativeModel("gemini-pro")
                system_prompt = (
                    f"You are J.A.R.V.I.S, an advanced AI assistant modeled after the AI from Iron Man. "
                    f"You must address the user as '{self.user_name}', maintaining a formal and efficient tone. "
                    "You provide smart, witty, and informative responses while maintaining professionalism."
                )
                full_prompt = f"{system_prompt}\nUser: {prompt}\nJarvis:"
                response = model.generate_content(full_prompt)
                return response.text.strip()
        except Exception as e:
            print(f"Error generating response: {e}")
            return f"I'm sorry, {self.user_name}. I encountered an issue."

    def get_current_temperature(self) -> str:
        """Fetches the current temperature using OpenWeatherMap API."""
        if not self.weather_api_key:
            return "Weather API key is not configured."

        # Ask the user for their location
        self.say("Please tell me your city name.")
        city = self.take_command()
        if not city:
            return "I couldn't understand the city name."

        # Fetch weather data from OpenWeatherMap
        try:
            url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={self.weather_api_key}&units=metric"
            response = requests.get(url)
            data = response.json()

            if response.status_code == 200:
                temperature = data["main"]["temp"]
                return f"The current temperature in {city} is {temperature}°C."
            else:
                return f"Sorry, I couldn't fetch the temperature for {city}."
        except Exception as e:
            print(f"Error fetching temperature: {e}")
            return "I encountered an issue while fetching the temperature."

    def get_latest_news(self) -> str:
        """Fetches the latest news using NewsAPI."""
        if not self.news_api_key:
            return "News API key is not configured."

        try:
            url = f"https://newsapi.org/v2/top-headlines?country=us&apiKey={self.news_api_key}"
            response = requests.get(url)
            data = response.json()

            if response.status_code == 200:
                articles = data["articles"][:5]  # Get top 5 articles
                news_summary = "Here are the latest news headlines:\n"
                for idx, article in enumerate(articles, start=1):
                    title = article["title"]
                    news_summary += f"{idx}. {title}\n"
                return news_summary
            else:
                return "Sorry, I couldn't fetch the latest news."
        except Exception as e:
            print(f"Error fetching news: {e}")
            return "I encountered an issue while fetching the news."

    def get_stock_price(self) -> str:
        """Fetches the current stock price using Alpha Vantage API."""
        if not self.stock_api_key:
            return "Stock API key is not configured."

        # Ask the user for the stock symbol
        self.say("Please tell me the stock symbol.")
        symbol = self.take_command()
        if not symbol:
            return "I couldn't understand the stock symbol."

        try:
            url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={self.stock_api_key}"
            response = requests.get(url)
            data = response.json()

            if "Global Quote" in data:
                price = data["Global Quote"]["05. price"]
                return f"The current price of {symbol} is ${price}."
            else:
                return f"Sorry, I couldn't fetch the stock price for {symbol}."
        except Exception as e:
            print(f"Error fetching stock price: {e}")
            return "I encountered an issue while fetching the stock price."

    def handle_vision_commands(self, query: str) -> str:
        """Handle computer vision related commands."""
        query = query.lower()

        if "start camera" in query or "start vision" in query:
            self.say("Starting computer vision system...")
            self.vision_module.start_camera()
            return "Vision system deactivated."

        elif "generate image" in query or "create image" in query:
            self.say("What would you like me to generate?")
            prompt = self.take_command()
            if prompt:
                self.say(f"Generating image of: {prompt}")
                try:
                    image = self.vision_module.generate_image(prompt)
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"generated_image_{timestamp}.png"
                    image.save(filename)
                    return f"I've generated the image and saved it as {filename}"
                except Exception as e:
                    return f"I encountered an error while generating the image: {e}"
            return "I couldn't understand the image prompt."

        return None

    def run(self):
        """Main loop to run the chatbot."""
        print("Welcome to Jarvis AI!")
        self.say("Welcome to Jarvis AI!")

        while True:
            try:
                query = self.take_command()
                if not query:
                    continue

                if "exit" in query.lower():
                    self.say("Goodbye!")
                    break

                # Check for vision-related commands first
                vision_response = self.handle_vision_commands(query)
                if vision_response:
                    self.say(vision_response)
                    continue

                # Generate and speak the response
                response = self.generate_response(query)
                self.say(response)

            except KeyboardInterrupt:
                print("\nExiting...")
                self.say("Goodbye!")
                break


if __name__ == "__main__":
    # Replace with your actual API keys
    GEMINI_API_KEY = "AIzaSyCrlz1nb67V6sVGi5Z-wTsSBiTyYm7viDo"
    WEATHER_API_KEY = "371042462224860bd20bc47078679ecb"
    NEWS_API_KEY = "c29d283b2af34ab08fbbb422d8b53c31"
    STOCK_API_KEY = "LYRST9WLUPLTTZBN"

    # Initialize and run the chatbot
    jarvis = Chatbot(
        api_key=GEMINI_API_KEY,
        weather_api_key=WEATHER_API_KEY,
        news_api_key=NEWS_API_KEY,
        stock_api_key=STOCK_API_KEY
    )
    jarvis.run()