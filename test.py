"""import time
from elevenlabs import generate, save, set_api_key  # Import necessary functions
import os

# Set your ElevenLabs API key (if required)
set_api_key("sk_c3cf3c18abbdf27d87947f76722b224280dce22179b6e83b")  # Replace with your actual API key

# Ensure the 'audio' directory exists
os.makedirs("audio", exist_ok=True)

# Your text to generate audio
response = "Hello, this is a test response."

try:
    # Start timing
    current_time = time.time()

    # Generate audio
    audio = generate(
        text=response,
        voice="Adam",
        model="eleven_monolingual_v1"
    )

    # Save audio to file
    save(audio, "audio/response.wav")

    # Calculate time taken
    audio_time = time.time() - current_time
    print(f"Finished generating audio in {audio_time:.2f} seconds.")

except Exception as e:
    # Log any errors
    print(f"An error occurred: {e}")"""

from elevenlabs.client import ElevenLabs

client = ElevenLabs(
    api_key="sk_c3cf3c18abbdf27d87947f76722b224280dce22179b6e83b"
)

# Generate audio as a stream
audio_stream = client.generate(
    text="Hello, this is ElevenLabs speaking!",
    voice="Brian",
    model="eleven_multilingual_v2",
    stream=True  # Enables streaming
)

# Save the audio file correctly
with open("output.mp3", "wb") as f:
    for chunk in audio_stream:  # Iterate over generator
        f.write(chunk)

# Play the saved file
import os
os.system("start output.mp3")  # Opens in default media player (Windows)
