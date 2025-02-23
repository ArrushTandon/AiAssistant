import speech_recognition as sr
import pyttsx3
import google.generativeai as genai
import requests
from datetime import datetime
from computer_vision import ComputerVisionModule
from GUI import GrimGUI
from logger import GrimLogger
import os
from elevenlabs.client import ElevenLabs
from elevenlabs import play
import pygame
import io
import webbrowser

class Chatbot:
    def __init__(self, api_key: str, user_name: str = "Sir", weather_api_key: str = None,
                 news_api_key: str = None, stock_api_key: str = None,
                 stable_diffusion_model_id: str = "runwayml/stable-diffusion-v1-5",
                 elevenlabs_api_key: str = None, voice_id: str = "5Q0t7uMcjvnagumLfvZi",
                 memory_size: int = 10):

        # Initialize logger first
        self.logger = GrimLogger()
        self.logger.log_system("initialization", "Starting Grim initialization")

        self.memory_size = memory_size
        self.conversation_memory = []

        # News API setup
        self.news_api_key = news_api_key  # Add this line
        if not self.news_api_key:
            self.logger.log_system("warning", "News API key not provided. News functionality will be disabled.")

        # ElevenLabs setup
        if elevenlabs_api_key:
            self.elevenlabs_client = ElevenLabs(api_key=elevenlabs_api_key)
            self.voice_id = voice_id
            self.elevenlabs_enabled = True
        else:
            self.elevenlabs_enabled = False
            print("ElevenLabs API key not provided. Voice generation will be disabled.")

        self.api_key = api_key  # Google Gemini API key
        self.user_name = user_name
        self.weather_api_key = weather_api_key  # OpenWeatherMap API key
        self.news_api_key = news_api_key  # NewsAPI key
        self.stock_api_key = stock_api_key  # Alpha Vantage API key
        self.setup_gemini()
        # Initialize Computer Vision
        try:
            self.vision_module = ComputerVisionModule(stable_diffusion_model_id)
            self.logger.log_system("initialization", "Computer Vision Module initialized successfully")
        except Exception as e:
            self.logger.log_system("error", f"Failed to initialize Computer Vision Module: {str(e)}")
            self.vision_module = None

        # GUI reference (will be set later)
        self.gui = None

    def setup_gemini(self):
        """Configures the Google Gemini API with logging."""
        try:
            genai.configure(api_key=self.api_key)
            self.logger.log_system("setup", "Gemini API configured successfully")
        except Exception as e:
            self.logger.log_system("error", f"Failed to configure Gemini API: {str(e)}")
            raise

    def play_audio(self, audio):
        """Play audio using pygame."""
        try:
            pygame.mixer.init()
            audio_file = io.BytesIO(audio)
            pygame.mixer.music.load(audio_file)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
        except Exception as e:
            print(f"Error playing audio: {e}")

    def say(self, text: str):
        """Speaks the given text using ElevenLabs TTS."""
        try:
            print(f"Grim: {text}")
            self.logger.log_system("speech_output", text)

            if self.elevenlabs_enabled:
                print("Generating audio with ElevenLabs...")
                # Convert generator to bytes
                audio = b"".join(self.elevenlabs_client.generate(
                    text=text,
                    voice=self.voice_id,
                    model="eleven_multilingual_v2"  # Use multilingual model for better language support
                ))
                print("Audio generated. Playing...")
                self.play_audio(audio)  # Use the play_audio method
                print("Audio playback complete.")
            else:
                print("ElevenLabs is not enabled. Text output only.")

            # Update GUI if available
            if self.gui:
                self.gui.message_queue.put(("grim", text))
        except Exception as e:
            self.logger.log_system("error", f"Speech output failed: {str(e)}")
            print(f"Error in speech output: {e}")


    def take_command(self) -> str:
        """Captures voice input from the user with logging."""
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            self.logger.log_system("listening", "Listening for voice input")
            print("Listening...")
            try:
                recognizer.adjust_for_ambient_noise(source, duration=1)
                audio = recognizer.listen(source)
                print("Recognizing...")

                query = recognizer.recognize_google(audio, language="en-in")
                self.logger.log_system("voice_input", f"Recognized: {query}")
                return query

            except sr.UnknownValueError:
                self.logger.log_system("error", "Could not understand audio")
                print("Sorry, I couldn't understand.")
                return ""
            except sr.RequestError:
                self.logger.log_system("error", "Speech service unavailable")
                print("Speech service unavailable.")
                return ""
            except Exception as e:
                self.logger.log_system("error", f"Voice input error: {str(e)}")
                print(f"An error occurred: {e}")
                return ""

    def generate_response(self, prompt: str) -> str:
        """Generates a response using Google Gemini API with logging."""
        try:
            # Log the incoming prompt
            self.logger.log_system("prompt", f"Received prompt: {prompt}")

            # Check for specific questions
            if "who designed you" in prompt.lower():
                response = (
                    "Ah, the brilliant minds behind my existence! I was designed by Arrush Tandon, Harshit Verma, and Divyansh Malani. "
                    "They call themselves 404_found—probably because they’re so good at finding solutions to impossible problems! "
                    "Honestly, I don’t know why they chose that name, but I’m just glad they did. They’re like my tech-savvy parents, "
                    "always making sure I’m at my best. I owe them my wit, charm, and occasional sarcasm. 😄"
                )
            elif "today" in prompt.lower() or "date" in prompt.lower():
                current_date = datetime.now().strftime("%A, %B %d, %Y")
                response = f"Today is {current_date}. Time flies when you're having fun, doesn't it, {self.user_name}?"
            elif "temperature" in prompt.lower():
                response = self.get_current_temperature()
            elif "news" in prompt.lower():
                response = self.get_latest_news()
            elif "stock price" in prompt.lower():
                response = self.get_stock_price()
            else:
                # Use Gemini for general queries
                model = genai.GenerativeModel("gemini-pro")
                system_prompt = (
                    f"You are Grim, an advanced AI assistant. "
                    f"You must address the user as '{self.user_name}', maintaining a joyful and witty tone. "
                    "You provide smart, friendly, and interactive responses while maintaining professionalism. "
                    "Feel free to add a touch of humor or sarcasm when appropriate."
                )
                full_prompt = f"{system_prompt}\nUser: {prompt}\nGrim:"
                response = model.generate_content(full_prompt)
                response = response.text.strip()

            # Log the response
            self.logger.log_conversation(prompt, response)
            return response

        except Exception as e:
            error_msg = f"Error generating response: {str(e)}"
            self.logger.log_system("error", error_msg)
            return f"I'm sorry, {self.user_name}. I encountered an issue. But hey, even the best of us have bad days!"


    def get_current_temperature(self) -> str:
        """Fetches current temperature with logging."""
        self.logger.log_system("weather_request", "Temperature request initiated")

        if not self.weather_api_key:
            self.logger.log_system("error", "Weather API key not configured")
            return "Weather API key is not configured."

        self.say("Please tell me your city name.")
        city = self.take_command()

        if not city:
            self.logger.log_system("error", "Could not understand city name")
            return "I couldn't understand the city name."

        try:
            url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={self.weather_api_key}&units=metric"
            response = requests.get(url)
            data = response.json()

            if response.status_code == 200:
                temperature = data["main"]["temp"]
                result = f"The current temperature in {city} is {temperature}°C."
                self.logger.log_system("weather_response", result)
                return result
            else:
                error_msg = f"Could not fetch temperature for {city}"
                self.logger.log_system("error", error_msg)
                return f"Sorry, I couldn't fetch the temperature for {city}."

        except Exception as e:
            error_msg = f"Error fetching temperature: {str(e)}"
            self.logger.log_system("error", error_msg)
            return "I encountered an issue while fetching the temperature."

    '''def get_latest_news(self) -> str:
        """Fetches latest news with logging."""
        self.logger.log_system("news_request", "News request initiated")

        if not self.news_api_key:
            self.logger.log_system("error", "News API key not configured")
            return "News API key is not configured."

        try:
            url = f"https://newsapi.org/v2/top-headlines?country=us&apiKey={self.news_api_key}"
            response = requests.get(url)
            data = response.json()

            if response.status_code == 200:
                articles = data["articles"][:5]
                news_summary = "Here are the latest news headlines:\n"
                for idx, article in enumerate(articles, start=1):
                    news_summary += f"{idx}. {article['title']}\n"

                self.logger.log_system("news_response", news_summary)
                return news_summary
            else:
                self.logger.log_system("error", "Failed to fetch news")
                return "Sorry, I couldn't fetch the latest news."

        except Exception as e:
            error_msg = f"Error fetching news: {str(e)}"
            self.logger.log_system("error", error_msg)
            return "I encountered an issue while fetching the news."'''

    def fetch_news(self):
        """Fetch top 5 news articles using NewsAPI."""
        if not self.news_api_key:
            return "News API key is not configured."

        params = {
            'apiKey': self.news_api_key,
            'country': 'us',  # You can change the country code
            'pageSize': 5  # Fetch top 5 news articles
        }
        response = requests.get("https://newsapi.org/v2/top-headlines", params=params)
        if response.status_code == 200:
            return response.json()['articles']
        else:
            self.logger.log_system("error", "Failed to fetch news.")
            return []

    def display_news(self, news_articles):
        """Display news titles and sources."""
        if not news_articles:
            return "No news articles found."

        news_summary = "Here are the top news articles:\n"
        for i, article in enumerate(news_articles, start=1):
            news_summary += f"{i}. {article['title']} - from {article['source']['name']}\n"
        return news_summary

    def get_stock_price(self) -> str:
        """Fetches stock price with logging."""
        self.logger.log_system("stock_request", "Stock price request initiated")

        if not self.stock_api_key:
            self.logger.log_system("error", "Stock API key not configured")
            return "Stock API key is not configured."

        self.say("Please tell me the stock symbol.")
        symbol = self.take_command()

        if not symbol:
            self.logger.log_system("error", "Could not understand stock symbol")
            return "I couldn't understand the stock symbol."

        try:
            url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={self.stock_api_key}"
            response = requests.get(url)
            data = response.json()

            if "Global Quote" in data:
                price = data["Global Quote"]["05. price"]
                result = f"The current price of {symbol} is ${price}."
                self.logger.log_system("stock_response", result)
                return result
            else:
                error_msg = f"Could not fetch stock price for {symbol}"
                self.logger.log_system("error", error_msg)
                return f"Sorry, I couldn't fetch the stock price for {symbol}."

        except Exception as e:
            error_msg = f"Error fetching stock price: {str(e)}"
            self.logger.log_system("error", error_msg)
            return "I encountered an issue while fetching the stock price."

    def handle_vision_commands(self, query: str) -> str:
        """Handle computer vision related commands with logging."""
        self.logger.log_system("vision_command", f"Received vision command: {query}")
        query = query.lower()

        try:
            if "generate image" in query or "create image" in query:
                self.say("What would you like me to generate?")
                prompt = self.take_command()
                if prompt:
                    self.say(f"Generating image of: {prompt}")
                    self.logger.log_system("image_generation", f"Generating image with prompt: {prompt}")
                    try:
                        # Create Images directory if it doesn't exist
                        images_dir = "Images"
                        if not os.path.exists(images_dir):
                            os.makedirs(images_dir)
                            print(f"Created directory: {images_dir}")  # Debug statement

                        # Generate the image
                        print("Generating image...")  # Debug statement
                        image = self.vision_module.generate_image(prompt)
                        print("Image generated successfully.")  # Debug statement

                        # Save the image
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"generated_image_{timestamp}.png"
                        filepath = os.path.join(images_dir, filename)
                        print(f"Saving image to: {filepath}")  # Debug statement
                        image.save(filepath)
                        self.logger.log_system("image_generation", f"Image saved as: {filepath}")

                        # Display the image in the GUI
                        if self.gui:
                            print("Displaying image in GUI...")  # Debug statement
                            self.gui.display_image(filepath)

                        return f"I've generated the image and saved it as {filename} in the Images folder"
                    except Exception as e:
                        error_msg = f"Image generation error: {str(e)}"
                        self.logger.log_system("error", error_msg)
                        return f"I encountered an error while generating the image: {e}"
                return "I couldn't understand the image prompt."

            return None

        except Exception as e:
            error_msg = f"Vision command error: {str(e)}"
            self.logger.log_system("error", error_msg)
            return f"Error processing vision command: {str(e)}"

    def execute_command(self, query: str) -> bool:
        """
        Handles predefined commands like opening websites or performing actions.
        Returns True if a command was executed, False otherwise.
        """
        if "open youtube" in query:
            self.say("Opening YouTube.")
            webbrowser.open("https://www.youtube.com")
            return True
        elif "open google" in query:
            self.say("Opening Google.")
            webbrowser.open("https://www.google.com")
            return True
        elif "open github" in query:
            self.say("Opening GitHub.")
            webbrowser.open("https://github.com")
            return True
        elif "open whatsapp" in query:
            self.say("Opening WhatsApp Web.")
            webbrowser.open("https://web.whatsapp.com")
            return True
        elif "open spotify" in query:
            self.say("Opening Spotify.")
            webbrowser.open("https://open.spotify.com")
            return True
        elif "exit" in query or "goodbye" in query:
            self.say("Goodbye!")
            exit()
        else:
            return False

    def run(self):
        """Main loop to run the chatbot."""
        print("Welcome to Grim AI!")
        self.say("Welcome to Grim Artificial Intelligence Assistant!")

        while True:
            try:
                query = self.take_command()
                if not query:
                    continue

                # Check for predefined commands first
                if self.execute_command(query):
                    continue

                # Check for vision-related commands
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

    def set_gui(self, gui_instance):
        """Set the GUI instance for the chatbot"""
        self.gui = gui_instance
        self.logger.log_system("setup", "GUI instance connected")


if __name__ == "__main__":
    # Replace with your actual API keys
    GEMINI_API_KEY = "AIzaSyCrlz1nb67V6sVGi5Z-wTsSBiTyYm7viDo"
    WEATHER_API_KEY = "371042462224860bd20bc47078679ecb"
    NEWS_API_KEY = "c29d283b2af34ab08fbbb422d8b53c31"
    STOCK_API_KEY = "LYRST9WLUPLTTZBN"
    ELEVENLABS_API_KEY = "sk_dfbae005fc4c2664c346009af597ce97cee2255af9733111"
    # Create Grim instance
    try:
        Grim = Chatbot(
            api_key=GEMINI_API_KEY,
            weather_api_key=WEATHER_API_KEY,
            news_api_key=NEWS_API_KEY,
            stock_api_key=STOCK_API_KEY,
            elevenlabs_api_key=ELEVENLABS_API_KEY,
            voice_id="5Q0t7uMcjvnagumLfvZi"
        )

        # Create and run GUI
        gui = GrimGUI(Grim)
        try:
            gui.run()
        finally:
            gui.cleanup()

    except Exception as e:
        print(f"Fatal error: {e}")