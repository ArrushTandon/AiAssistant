"""import customtkinter as ctk
import threading
import queue
import sounddevice as sd
import numpy as np
import speech_recognition as sr
import pvporcupine
import pyaudio
import struct
from PIL import Image, ImageTk
import os


class GrimGUI:
    def __init__(self, grim_instance):
        self.grim = grim_instance
        self.message_queue = queue.Queue()
        self.setup_window()
        self.setup_voice_detection()
        self.is_listening = False

    def display_image(self, image_path: str):
        #Display the generated image in the GUI.
        try:
            # Load the image
            image = Image.open(image_path)
            image.thumbnail((400, 400))  # Resize the image to fit in the GUI

            # Convert the image to a format Tkinter can display
            image_tk = ImageTk.PhotoImage(image)

            # Create a label to display the image
            image_label = ctk.CTkLabel(self.root, image=image_tk, text="")
            image_label.image = image_tk  # Keep a reference to avoid garbage collection
            image_label.pack(pady=10)

            print(f"Image displayed: {image_path}")  # Debug statement
        except Exception as e:
            print(f"Error displaying image: {e}")  # Debug statement

    def setup_window(self):
        # Configure the window
        self.root = ctk.CTk()
        self.root.title("G.R.I.M")
        self.root.geometry("1000x600")
        ctk.set_appearance_mode("dark")

        # Create main containers
        self.create_sidebar()
        self.create_chat_area()
        self.create_input_area()

        # Start the message processing thread
        self.processing_thread = threading.Thread(target=self.process_messages, daemon=True)
        self.processing_thread.start()

    def create_sidebar(self):
        # Sidebar frame
        sidebar = ctk.CTkFrame(self.root, width=200)
        sidebar.pack(side="left", fill="y", padx=10, pady=10)

        # Logo or title
        title = ctk.CTkLabel(sidebar, text="G.R.I.M", font=("Arial", 24, "bold"))
        title.pack(pady=20)

        # Voice activation status
        self.status_label = ctk.CTkLabel(sidebar, text="Listening for 'Hey Grim'")
        self.status_label.pack(pady=10)

        # Upload button
        upload_btn = ctk.CTkButton(sidebar, text="Upload File", command=self.upload_file)
        upload_btn.pack(pady=10)

        # Settings button
        settings_btn = ctk.CTkButton(sidebar, text="Settings", command=self.open_settings)
        settings_btn.pack(pady=10)

    def create_chat_area(self):
        # Chat display area
        chat_frame = ctk.CTkFrame(self.root)
        chat_frame.pack(side="top", fill="both", expand=True, padx=10, pady=10)

        self.chat_display = ctk.CTkTextbox(chat_frame, wrap="word", font=("Arial", 12))
        self.chat_display.pack(fill="both", expand=True, padx=5, pady=5)
        self.chat_display.configure(state="disabled")

    def create_input_area(self):
        # Input area frame
        input_frame = ctk.CTkFrame(self.root)
        input_frame.pack(side="bottom", fill="x", padx=10, pady=10)

        # Text input
        self.input_field = ctk.CTkEntry(input_frame, placeholder_text="Type your message...")
        self.input_field.pack(side="left", fill="x", expand=True, padx=5)
        self.input_field.bind("<Return>", self.send_message)

        # Send button
        send_btn = ctk.CTkButton(input_frame, text="Send", command=self.send_message)
        send_btn.pack(side="right", padx=5)

        # Voice input button
        voice_btn = ctk.CTkButton(input_frame, text="🎤", width=40, command=self.toggle_voice_input)
        voice_btn.pack(side="right", padx=5)

    def setup_voice_detection(self):
        try:
            # Initialize Porcupine wake word detector with the custom keyword file
            self.porcupine = pvporcupine.create(
                access_key='WvCbkXNXfV1Oy++xXrpUq4vmWulTWru5tLjpzOXyhEZvoatk7idAmQ==',
                # Replace with your Porcupine access key
                keyword_paths=[r"C:/Users/arrus/PycharmProjects/JarvisAI/grim.ppn"]  # Use the custom keyword file
            )
            print("Porcupine initialized successfully with custom keyword 'grim'.")

            # Initialize PyAudio
            self.audio = pyaudio.PyAudio()
            self.stream = self.audio.open(
                rate=self.porcupine.sample_rate,
                channels=1,
                format=pyaudio.paInt16,
                input=True,
                frames_per_buffer=self.porcupine.frame_length
            )
            print("PyAudio initialized successfully.")

            # Start wake word detection thread
            self.wake_thread = threading.Thread(target=self.detect_wake_word, daemon=True)
            self.wake_thread.start()
            print("Wake word detection thread started.")

        except Exception as e:
            print(f"Error setting up voice detection: {e}")
            self.status_label.configure(text="Voice detection unavailable")

    def detect_wake_word(self):
        #Continuously listen for the wake word.
        while True:
            try:
                pcm = self.stream.read(self.porcupine.frame_length)
                pcm = struct.unpack_from("h" * self.porcupine.frame_length, pcm)

                keyword_index = self.porcupine.process(pcm)
                if keyword_index >= 0:
                    print("Wake word detected!")
                    self.root.after(0, self.handle_wake_word)

            except Exception as e:
                print(f"Error in wake word detection: {e}")
                break

    def handle_wake_word(self):
        #Handle wake word detection
        self.status_label.configure(text="Listening...")
        self.toggle_voice_input()

    def toggle_voice_input(self):
        #Toggle voice input on/off
        if not self.is_listening:
            self.is_listening = True
            threading.Thread(target=self.listen_for_command, daemon=True).start()
        else:
            self.is_listening = False
            self.status_label.configure(text="Listening for 'Hey Grim'")

    def listen_for_command(self):
        #Listen for voice command
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            try:
                audio = recognizer.listen(source, timeout=5)
                command = recognizer.recognize_google(audio)
                self.message_queue.put(("user", command))
                self.process_command(command)
            except sr.WaitTimeoutError:
                self.status_label.configure(text="Listening for 'Hey Grim'")
            except Exception as e:
                print(f"Error in voice recognition: {e}")
                self.status_label.configure(text="Listening for 'Hey Grim'")
        self.is_listening = False

    def send_message(self, event=None):
        #Send a text message
        message = self.input_field.get().strip()
        if message:
            self.input_field.delete(0, 'end')
            self.message_queue.put(("user", message))
            self.process_command(message)

    def process_command(self, command):
        #Updated process_command method with logging
        self.grim.logger.log_system("gui_command", command)
        response = self.grim.generate_response(command)
        self.message_queue.put(("grim", response))
        self.grim.say(response)

    def process_messages(self):
        #Process messages in the queue and update GUI
        while True:
            try:
                sender, message = self.message_queue.get()
                self.update_chat_display(sender, message)
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error processing message: {e}")

    def update_chat_display(self, sender, message):
        #Updated update_chat_display method with logging#
        self.chat_display.configure(state="normal")
        self.chat_display.insert("end", f"\n{sender.title()}: {message}\n")
        self.chat_display.configure(state="disabled")
        self.chat_display.see("end")
        self.grim.logger.log_system("chat_display_update",
                                      {"sender": sender, "message": message})

    def upload_file(self):
        #Handle file upload
        file_path = ctk.filedialog.askopenfilename()
        if file_path:
            file_name = os.path.basename(file_path)
            self.message_queue.put(("system", f"File uploaded: {file_name}"))
            # Add your file processing logic here

    def open_settings(self):
        #Open settings window
        settings_window = ctk.CTkToplevel(self.root)
        settings_window.title("Settings")
        settings_window.geometry("400x300")

        # Add your settings controls here

    def run(self):
        #Start the GUI
        self.root.mainloop()

    def cleanup(self):
        #Clean up resources
        if hasattr(self, 'porcupine'):
            self.porcupine.delete()
        if hasattr(self, 'stream'):
            self.stream.close()
        if hasattr(self, 'audio'):
            self.audio.terminate()"""

import customtkinter as ctk
import threading
import queue
import os
import speech_recognition as sr
import pvporcupine
import pyaudio
import struct
from PIL import Image, ImageTk
from datetime import datetime


class GrimGUI:
    def __init__(self, grim_instance):
        self.grim = grim_instance
        self.message_queue = queue.Queue()
        self.is_listening = False
        self.setup_window()
        self.setup_voice_detection()

    def setup_window(self):
        """Configure the main window."""
        # Set appearance mode and color theme
        ctk.set_appearance_mode("dark")  # Options: "dark", "light", "system"
        ctk.set_default_color_theme("blue")  # Options: "blue", "green", "dark-blue"

        # Create the main window
        self.root = ctk.CTk()
        self.root.title("G.R.I.M - AI Assistant")
        self.root.geometry("1000x600")
        self.root.resizable(True, True)

        # Create main containers
        self.create_sidebar()
        self.create_chat_area()
        self.create_input_area()

        # Start the message processing thread
        self.processing_thread = threading.Thread(target=self.process_messages, daemon=True)
        self.processing_thread.start()

    def create_sidebar(self):
        """Create the sidebar with controls."""
        sidebar = ctk.CTkFrame(self.root, width=200, corner_radius=10)
        sidebar.pack(side="left", fill="y", padx=10, pady=10)

        # Logo or title
        title = ctk.CTkLabel(sidebar, text="G.R.I.M", font=("Arial", 24, "bold"))
        title.pack(pady=20)

        # Voice activation status
        self.status_label = ctk.CTkLabel(sidebar, text="Listening for 'Hey Grim'", font=("Arial", 12))
        self.status_label.pack(pady=10)

        # Upload button
        upload_btn = ctk.CTkButton(sidebar, text="Upload File", command=self.upload_file)
        upload_btn.pack(pady=10)

        # Settings button
        settings_btn = ctk.CTkButton(sidebar, text="Settings", command=self.open_settings)
        settings_btn.pack(pady=10)

    def create_chat_area(self):
        """Create the chat display area."""
        chat_frame = ctk.CTkFrame(self.root, corner_radius=10)
        chat_frame.pack(side="top", fill="both", expand=True, padx=10, pady=10)

        # Chat display
        self.chat_display = ctk.CTkTextbox(chat_frame, wrap="word", font=("Arial", 14))
        self.chat_display.pack(fill="both", expand=True, padx=5, pady=5)
        self.chat_display.configure(state="disabled")

    def create_input_area(self):
        """Create the input area."""
        input_frame = ctk.CTkFrame(self.root, corner_radius=10)
        input_frame.pack(side="bottom", fill="x", padx=10, pady=10)

        # Text input
        self.input_field = ctk.CTkEntry(input_frame, placeholder_text="Type your message...", font=("Arial", 14))
        self.input_field.pack(side="left", fill="x", expand=True, padx=5)
        self.input_field.bind("<Return>", self.send_message)

        # Send button
        send_btn = ctk.CTkButton(input_frame, text="Send", command=self.send_message)
        send_btn.pack(side="right", padx=5)

        # Voice input button
        voice_btn = ctk.CTkButton(input_frame, text="🎤", width=40, command=self.toggle_voice_input)
        voice_btn.pack(side="right", padx=5)

    def setup_voice_detection(self):
        """Initialize Porcupine for wake word detection."""
        try:
            # Initialize Porcupine wake word detector with the custom keyword file
            self.porcupine = pvporcupine.create(
                access_key='WvCbkXNXfV1Oy++xXrpUq4vmWulTWru5tLjpzOXyhEZvoatk7idAmQ==',  # Replace with your Porcupine access key
                keyword_paths=[r"C:\Users\arrus\PycharmProjects\JarvisAI\grim.ppn"]  # Use the custom keyword file
            )
            print("Porcupine initialized successfully with custom keyword 'grim'.")

            # Initialize PyAudio
            self.audio = pyaudio.PyAudio()
            self.stream = self.audio.open(
                rate=self.porcupine.sample_rate,
                channels=1,
                format=pyaudio.paInt16,
                input=True,
                frames_per_buffer=self.porcupine.frame_length
            )
            print("PyAudio initialized successfully.")

            # Start wake word detection thread
            self.wake_thread = threading.Thread(target=self.detect_wake_word, daemon=True)
            self.wake_thread.start()
            print("Wake word detection thread started.")

        except Exception as e:
            print(f"Error setting up voice detection: {e}")
            self.status_label.configure(text="Voice detection unavailable")

    def detect_wake_word(self):
        """Continuously listen for the wake word."""
        while True:
            try:
                pcm = self.stream.read(self.porcupine.frame_length)
                pcm = struct.unpack_from("h" * self.porcupine.frame_length, pcm)

                keyword_index = self.porcupine.process(pcm)
                if keyword_index >= 0:
                    print("Wake word detected!")  # Debug statement
                    self.root.after(0, self.handle_wake_word)

            except Exception as e:
                print(f"Error in wake word detection: {e}")  # Debug statement
                break

    def handle_wake_word(self):
        """Handle wake word detection."""
        self.status_label.configure(text="Listening...")
        self.toggle_voice_input()

    def toggle_voice_input(self):
        """Toggle voice input on/off."""
        if not self.is_listening:
            self.is_listening = True
            threading.Thread(target=self.listen_for_command, daemon=True).start()
        else:
            self.is_listening = False
            self.status_label.configure(text="Listening for 'Hey Grim'")

    def listen_for_command(self):
        """Listen for voice command."""
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            try:
                print("Listening for voice input...")
                recognizer.adjust_for_ambient_noise(source, duration=1)
                audio = recognizer.listen(source, timeout=5)
                print("Recognizing...")
                query = recognizer.recognize_google(audio, language="en-US")
                print(f"Recognized: {query}")
                self.message_queue.put(("user", query))
                self.process_command(query)
            except sr.UnknownValueError:
                print("Could not understand audio.")
                self.status_label.configure(text="Listening for 'Hey Grim'")
            except sr.RequestError:
                print("Speech service unavailable.")
                self.status_label.configure(text="Listening for 'Hey Grim'")
            except Exception as e:
                print(f"Error in voice input: {e}")
                self.status_label.configure(text="Listening for 'Hey Grim'")
        self.is_listening = False
        self.status_label.configure(text="Listening for 'Hey Grim'")

    def send_message(self, event=None):
        """Send a text message."""
        message = self.input_field.get().strip()
        if message:
            self.input_field.delete(0, 'end')
            self.message_queue.put(("user", message))
            self.process_command(message)

    def process_command(self, command):
        """Process the user's command and update the chat display."""
        self.grim.logger.log_system("gui_command", command)
        response = self.grim.generate_response(command)
        self.message_queue.put(("grim", response))
        self.grim.say(response)

    def process_messages(self):
        """Process messages in the queue and update the chat display."""
        while True:
            try:
                sender, message = self.message_queue.get()
                self.update_chat_display(sender, message)
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error processing message: {e}")

    def update_chat_display(self, sender, message):
        """Update the chat display with a new message."""
        self.chat_display.configure(state="normal")
        self.chat_display.insert("end", f"\n{sender.title()}: {message}\n")
        self.chat_display.configure(state="disabled")
        self.chat_display.see("end")
        self.grim.logger.log_system("chat_display_update", {"sender": sender, "message": message})

    def display_image(self, image_path: str):
        """Display the generated image in the GUI."""
        try:
            # Verify file exists
            if not os.path.exists(image_path):
                print(f"Error: Image file not found at {image_path}")
                return

            # Load and resize image
            image = Image.open(image_path)

            # Calculate resize dimensions while maintaining aspect ratio
            max_size = (400, 400)
            ratio = min(max_size[0] / image.width, max_size[1] / image.height)
            new_size = (int(image.width * ratio), int(image.height * ratio))
            image = image.resize(new_size, Image.Resampling.LANCZOS)

            # Convert to PhotoImage
            image_tk = ImageTk.PhotoImage(image)

            # Create new frame for image
            image_frame = ctk.CTkFrame(self.chat_display)
            self.chat_display.configure(state="normal")
            self.chat_display.window_create("end", window=image_frame)
            self.chat_display.insert("end", "\n")
            self.chat_display.configure(state="disabled")

            # Create and pack image label
            image_label = ctk.CTkLabel(image_frame, image=image_tk, text="")
            image_label.image = image_tk  # Keep reference
            image_label.pack(pady=10)

            # Scroll to show new image
            self.chat_display.see("end")
            print(f"Image displayed successfully from: {image_path}")

        except Exception as e:
            print(f"Error displaying image: {e}")
            self.update_chat_display("system", "Failed to display the generated image.")
    def upload_file(self):
        """Handle file upload."""
        file_path = ctk.filedialog.askopenfilename()
        if file_path:
            file_name = os.path.basename(file_path)
            self.message_queue.put(("system", f"File uploaded: {file_name}"))
            # Add your file processing logic here

    def open_settings(self):
        """Open settings window."""
        settings_window = ctk.CTkToplevel(self.root)
        settings_window.title("Settings")
        settings_window.geometry("400x300")

        # Add your settings controls here

    def run(self):
        """Start the GUI."""
        self.root.mainloop()

    def cleanup(self):
        """Clean up resources."""
        if hasattr(self, 'porcupine'):
            self.porcupine.delete()
        if hasattr(self, 'stream'):
            self.stream.close()
        if hasattr(self, 'audio'):
            self.audio.terminate()