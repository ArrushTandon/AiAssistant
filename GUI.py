import customtkinter as ctk
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


class JarvisGUI:
    def __init__(self, jarvis_instance):
        self.jarvis = jarvis_instance
        self.setup_window()
        self.setup_voice_detection()
        self.message_queue = queue.Queue()
        self.is_listening = False

    def setup_window(self):
        # Configure the window
        self.root = ctk.CTk()
        self.root.title("J.A.R.V.I.S")
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
        title = ctk.CTkLabel(sidebar, text="J.A.R.V.I.S", font=("Arial", 24, "bold"))
        title.pack(pady=20)

        # Voice activation status
        self.status_label = ctk.CTkLabel(sidebar, text="Listening for 'Hey Jarvis'")
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
            # Initialize Porcupine wake word detector
            self.porcupine = pvporcupine.create(
                access_key='WvCbkXNXfV1Oy++xXrpUq4vmWulTWru5tLjpzOXyhEZvoatk7idAmQ==',  # Porcupine Access key
                keywords=['jarvis']
            )

            # Initialize PyAudio
            self.audio = pyaudio.PyAudio()
            self.stream = self.audio.open(
                rate=self.porcupine.sample_rate,
                channels=1,
                format=pyaudio.paInt16,
                input=True,
                frames_per_buffer=self.porcupine.frame_length
            )

            # Start wake word detection thread
            self.wake_thread = threading.Thread(target=self.detect_wake_word, daemon=True)
            self.wake_thread.start()

        except Exception as e:
            print(f"Error setting up voice detection: {e}")
            self.status_label.configure(text="Voice detection unavailable")

    def detect_wake_word(self):
        """Continuously listen for the wake word"""
        while True:
            try:
                pcm = self.stream.read(self.porcupine.frame_length)
                pcm = struct.unpack_from("h" * self.porcupine.frame_length, pcm)

                keyword_index = self.porcupine.process(pcm)
                if keyword_index >= 0:
                    self.root.after(0, self.handle_wake_word)

            except Exception as e:
                print(f"Error in wake word detection: {e}")
                break

    def handle_wake_word(self):
        """Handle wake word detection"""
        self.status_label.configure(text="Listening...")
        self.toggle_voice_input()

    def toggle_voice_input(self):
        """Toggle voice input on/off"""
        if not self.is_listening:
            self.is_listening = True
            threading.Thread(target=self.listen_for_command, daemon=True).start()
        else:
            self.is_listening = False
            self.status_label.configure(text="Listening for 'Hey Jarvis'")

    def listen_for_command(self):
        """Listen for voice command"""
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            try:
                audio = recognizer.listen(source, timeout=5)
                command = recognizer.recognize_google(audio)
                self.message_queue.put(("user", command))
                self.process_command(command)
            except sr.WaitTimeoutError:
                self.status_label.configure(text="Listening for 'Hey Jarvis'")
            except Exception as e:
                print(f"Error in voice recognition: {e}")
                self.status_label.configure(text="Listening for 'Hey Jarvis'")
        self.is_listening = False

    def send_message(self, event=None):
        """Send a text message"""
        message = self.input_field.get().strip()
        if message:
            self.input_field.delete(0, 'end')
            self.message_queue.put(("user", message))
            self.process_command(message)

    def process_command(self, command):
        """Updated process_command method with logging"""
        self.jarvis.logger.log_system("gui_command", command)
        response = self.jarvis.generate_response(command)
        self.message_queue.put(("jarvis", response))
        self.jarvis.say(response)

    def process_messages(self):
        """Process messages in the queue and update GUI"""
        while True:
            try:
                sender, message = self.message_queue.get()
                self.update_chat_display(sender, message)
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error processing message: {e}")

    def update_chat_display(self, sender, message):
        """Updated update_chat_display method with logging"""
        self.chat_display.configure(state="normal")
        self.chat_display.insert("end", f"\n{sender.title()}: {message}\n")
        self.chat_display.configure(state="disabled")
        self.chat_display.see("end")
        self.jarvis.logger.log_system("chat_display_update",
                                      {"sender": sender, "message": message})

    def upload_file(self):
        """Handle file upload"""
        file_path = ctk.filedialog.askopenfilename()
        if file_path:
            file_name = os.path.basename(file_path)
            self.message_queue.put(("system", f"File uploaded: {file_name}"))
            # Add your file processing logic here

    def open_settings(self):
        """Open settings window"""
        settings_window = ctk.CTkToplevel(self.root)
        settings_window.title("Settings")
        settings_window.geometry("400x300")

        # Add your settings controls here

    def run(self):
        """Start the GUI"""
        self.root.mainloop()

    def cleanup(self):
        """Clean up resources"""
        if hasattr(self, 'porcupine'):
            self.porcupine.delete()
        if hasattr(self, 'stream'):
            self.stream.close()
        if hasattr(self, 'audio'):
            self.audio.terminate()