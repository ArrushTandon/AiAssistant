import speech_recognition as sr
import pyttsx3
import google.generativeai as genai
import requests
from datetime import datetime
import re
from email_agent import EmailAgent
from typing import List, Dict, Optional
from collections import defaultdict

class Chatbot:
    def __init__(self, api_key: str, user_name: str = "Arrush", weather_api_key: str = None, 
                 news_api_key: str = None, stock_api_key: str = None):
        self.api_key = api_key
        self.user_name = user_name
        self.weather_api_key = weather_api_key
        self.news_api_key = news_api_key
        self.stock_api_key = stock_api_key
        self.engine = pyttsx3.init()
        self.setup_gemini()
        self.email_context = {
            "last_search": None,
            "days_ago": 0,
            "last_results": [],  # Store last email search results
            "current_email": None  # Store currently focused email
        }
        
        # Initialize email agent with retry logic
        max_attempts = 3
        for attempt in range(max_attempts):
            self.email_agent = EmailAgent()
            self.email_agent.login()
            if self.email_agent.logged_in:
                break
            elif attempt < max_attempts - 1:
                print(f"Login attempt {attempt + 1} failed. Please try again.")
            else:
                print("Email login failed. Email features will be disabled.")

    def setup_gemini(self):
        """Configures the Google Gemini API."""
        genai.configure(api_key=self.api_key)

    def say(self, text: str):
        """Speaks the given text using pyttsx3."""
        print(f"Jarvis: {text}")
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
                print(f"User: {query}")
                return query.lower()
            except sr.UnknownValueError:
                print("Sorry, I couldn't understand.")
                return ""
            except sr.RequestError:
                print("Speech service unavailable.")
                return ""
            except Exception as e:
                print(f"An error occurred: {e}")
                return ""

    def handle_email_query(self, query: str) -> str:
        """Handles email-related queries with enhanced intelligence."""
        if not self.email_agent.logged_in:
            return "Email login failed. Please check your credentials."

        # Handle "summarize my emails" command
        if "summarize my emails" in query.lower():
            email_ids = self.email_agent.get_emails_by_date(0)  # Fetch emails from today
            if not email_ids:
                return "No emails found for today."

            emails = []
            for email_id in email_ids:
                email_details = self.email_agent.get_email_details(email_id)
                if email_details:
                    emails.append(email_details)

            if not emails:
                return "No emails found for today."

            response = "Here is a summary of your emails today:\n\n"
            for email in emails:
                response += f"From: {email['sender']}\n"
                response += f"Subject: {email['subject']}\n"
                response += f"Summary: {email['summary']}\n\n"
            
            # Display categories after summaries
            response += "\nCategories:\n"
            for email in emails:
                response += f"Subject: {email['subject']}\n"
                response += f"Categories: {', '.join(email['categories']) or 'No category'}\n\n"
            
            return response

        # Handle numbered email selection
        number_match = re.search(r'(?:number|#)\s*(\d+)', query.lower())
        if number_match:
            number = int(number_match.group(1))
            if not self.email_context["last_results"]:
                return "Please search for emails first before selecting a number."
            if number < 1 or number > len(self.email_context["last_results"]):
                return f"Please select a number between 1 and {len(self.email_context['last_results'])}."
            
            email = self.email_context["last_results"][number - 1]
            self.email_context["current_email"] = email
            return self.format_detailed_email(email)

        # Handle request for similar emails
        if "similar" in query.lower() and self.email_context["current_email"]:
            similar_emails = self.email_agent.find_similar_emails(
                self.email_context["current_email"]["id"]
            )
            if not similar_emails:
                return "No similar emails found."
            
            self.email_context["last_results"] = similar_emails
            return self.format_email_list(similar_emails, "Similar emails found")

        # Handle full content request
        if "full content" in query.lower() and self.email_context["current_email"]:
            email = self.email_context["current_email"]
            return f"Full Email Content:\n\nFrom: {email['sender']}\nSubject: {email['subject']}\nDate: {email['date']}\n\n{email['body']}"

        # Handle regular email search
        days_ago = 0
        if "last month" in query or "past month" in query:
            days_ago = 30
        elif "last week" in query or "past week" in query:
            days_ago = 7

        category = None
        if "job" in query:
            category = "job"
        elif "course" in query or "education" in query:
            category = "education"

        email_ids = self.email_agent.get_emails_by_date(days_ago)
        if not email_ids:
            return f"No emails found in the specified time period."

        # Fetch and summarize emails
        emails = []
        for email_id in email_ids:
            email_details = self.email_agent.get_email_details(email_id)
            if email_details:
                emails.append(email_details)

        # Categorize emails
        categorized_emails = defaultdict(list)
        for email in emails:
            if category and category in email['categories']:
                categorized_emails[category].append(email)
            else:
                categorized_emails['other'].append(email)

        self.email_context = {
            "last_search": category,
            "days_ago": days_ago,
            "last_results": emails,
            "current_email": None
        }

        if category:
            emails = categorized_emails.get(category, [])
            if not emails:
                response = f"No {category}-related emails found in the specified time period.\n"
                response += "Would you like me to extend the search to older emails? (Yes/No)"
                return response

            self.email_context["last_results"] = emails
            return self.format_email_list(emails, f"{category}-related emails")
        else:
            total_emails = len(email_ids)
            response = f"Email Summary (Total: {total_emails}):\n\n"
            response += f"Job-related: {len(categorized_emails['job'])} emails\n"
            response += f"Education-related: {len(categorized_emails['education'])} emails\n"
            response += f"Other: {len(categorized_emails['other'])} emails\n\n"
            response += "Would you like to see details for any specific category?"
            return response

    def format_detailed_email(self, email: Dict) -> str:
        """Format a detailed view of a single email with summary."""
        response = f"Detailed Email View:\n\n"
        response += f"From: {email['sender']}\n"
        response += f"Subject: {email['subject']}\n"
        response += f"Date: {email['date']}\n"
        response += f"\n{email['summary']}\n"
        response += "\nYou can:\n"
        response += "1. Say 'show similar emails' to find related emails\n"
        response += "2. Say 'show full content' to see the complete email\n"
        return response

    def format_email_list(self, emails: List[Dict], title: str) -> str:
        """Format a list of emails with numbers."""
        response = f"{title} ({len(emails)} found):\n\n"
        for idx, email in enumerate(emails[:10], 1):
            response += (f"{idx}. From: {email['sender']}\n"
                       f"   Subject: {email['subject']}\n"
                       f"   Date: {email['date']}\n\n")
        response += "\nYou can:\n"
        response += "1. Select an email by saying 'show email number X'\n"
        response += "2. Ask for more results if available\n"
        return response

    def generate_response(self, prompt: str) -> str:
        """Generates a response using various APIs based on the query."""
        try:
            # Handle email-related queries
            if any(word in prompt for word in ["email", "mail"]):
                return self.handle_email_query(prompt)
            
            # Handle other queries (weather, news, stocks)
            if "weather" in prompt or "temperature" in prompt:
                return self.get_current_temperature()
            elif "news" in prompt:
                return self.get_latest_news()
            elif "stock" in prompt:
                return self.get_stock_price()
            
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
            return f"I apologize, {self.user_name}. I encountered an issue processing your request."

    def get_current_temperature(self) -> str:
        """Fetches the current temperature using OpenWeatherMap API."""
        if not self.weather_api_key:
            return "Weather API key is not configured."

        self.say("Please tell me your city name.")
        city = self.take_command()
        
        if not city:
            return "I couldn't understand the city name."

        try:
            url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={self.weather_api_key}&units=metric"
            response = requests.get(url)
            data = response.json()

            if response.status_code == 200:
                temperature = data["main"]["temp"]
                description = data["weather"][0]["description"]
                humidity = data["main"]["humidity"]
                feels_like = data["main"]["feels_like"]
                return (f"The current weather in {city}:\n"
                       f"Temperature: {temperature}°C\n"
                       f"Feels like: {feels_like}°C\n"
                       f"Conditions: {description}\n"
                       f"Humidity: {humidity}%")
            else:
                return f"Sorry, I couldn't fetch the weather for {city}."
        except Exception as e:
            print(f"Error fetching temperature: {e}")
            return "I encountered an issue while fetching the weather data."

    def get_latest_news(self) -> str:
        """Fetches the latest news using NewsAPI."""
        if not self.news_api_key:
            return "News API key is not configured."

        try:
            url = f"https://newsapi.org/v2/top-headlines?country=us&apiKey={self.news_api_key}"
            response = requests.get(url)
            data = response.json()

            if response.status_code == 200:
                articles = data["articles"][:5]
                news_summary = "Here are the latest news headlines:\n\n"
                for idx, article in enumerate(articles, start=1):
                    title = article["title"]
                    source = article["source"]["name"]
                    news_summary += f"{idx}. {title} ({source})\n"
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
                change = data["Global Quote"]["09. change"]
                change_percent = data["Global Quote"]["10. change percent"]
                return f"Stock information for {symbol.upper()}:\nPrice: ${price}\nChange: ${change} ({change_percent})"
            else:
                return f"Sorry, I couldn't fetch the stock price for {symbol}."
        except Exception as e:
            print(f"Error fetching stock price: {e}")
            return "I encountered an issue while fetching the stock price."

    def close(self):
        """Closes all connections."""
        if self.email_agent:
            self.email_agent.close()

    def run(self):
        """Main loop to run the chatbot."""
        startup_message = f"Welcome {self.user_name}! I am JARVIS, your personal AI assistant. How may I help you today?"
        print(startup_message)
        self.say(startup_message)

        try:
            while True:
                query = self.take_command()
                if not query:
                    continue

                if "exit" in query or "goodbye" in query or "bye" in query:
                    farewell = f"Goodbye, {self.user_name}! Have a great day!"
                    self.say(farewell)
                    break

                response = self.generate_response(query)
                self.say(response)

        except KeyboardInterrupt:
            print("\nShutting down...")
            self.say(f"Goodbye, {self.user_name}!")
        finally:
            self.close()


if __name__ == "__main__":
    # Your API keys
    GEMINI_API_KEY = "AIzaSyCrlz1nb67V6sVGi5Z-wTsSBiTyYm7viDo"
    WEATHER_API_KEY = "371042462224860bd20bc47078679ecb"
    NEWS_API_KEY = "c29d283b2af34ab08fbbb422d8b53c31"
    STOCK_API_KEY = "LYRST9WLUPLTTZBN"

    # Initialize and run the chatbot
    jarvis = Chatbot(
        api_key=GEMINI_API_KEY,
        user_name="Arrush",
        weather_api_key=WEATHER_API_KEY,
        news_api_key=NEWS_API_KEY,
        stock_api_key=STOCK_API_KEY
    )
    jarvis.run()