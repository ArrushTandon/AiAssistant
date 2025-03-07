# GRIM AI Assistant

A sophisticated AI assistant GRIM, featuring voice interaction, computer vision, and real-time data processing capabilities.

## Features

1. **Voice Interaction**
   - Wake word detection ("Hey Grim")
   - Natural speech recognition
   - Text-to-speech responses with configurable voices
   - Continuous listening mode

2. **Computer Vision Capabilities**
   - Real-time object detection using YOLOv8
   - Face detection and tracking via MediaPipe
   - AI image generation using Stable Diffusion
   - Optimized for NVIDIA GPUs (GTX 1650 and above)

3. **Real-time Data Integration**
   - Weather updates via OpenWeatherMap
   - Live news headlines from NewsAPI
   - Stock market data through Alpha Vantage
   - Customizable data refresh intervals

4. **Modern GUI Interface**
   - Dark-themed CustomTkinter interface
   - Real-time chat display with conversation history
   - File upload and processing capabilities
   - Configurable settings panel
   - Visual feedback for voice activation

5. **Comprehensive Logging System**
   - JSON-based session logging
   - Conversation history tracking
   - System event monitoring
   - Vision system logging
   - Error tracking and debugging support

### System Requirements

#### Minimum Hardware Requirements
- CPU: Intel i5/AMD Ryzen 5 or better
- RAM: 8GB minimum, 16GB recommended
- Storage: 2GB free space
- GPU: NVIDIA GTX 1650 or better (for computer vision features)
- Microphone: Required for voice interaction
- Camera: Required for computer vision features

#### Software Requirements
- Python 3.12 or later
- CUDA Toolkit 11.8 or later (for GPU support)
- Operating System:
  - Windows 10/11
  - Ubuntu 20.04 or later
  - macOS 12 or later

### Installation

1. **Core Dependencies**
```bash
pip install -r requirements.txt
```

2. **Platform-Specific Setup**

**Windows:**
```bash
# All dependencies included in requirements.txt
```

3. **API Configuration**
Create a `.env` file with your API keys:
```env
GEMINI_API_KEY=your_gemini_key
WEATHER_API_KEY=your_openweathermap_key
NEWS_API_KEY=your_newsapi_key
STOCK_API_KEY=your_alphavantage_key
PORCUPINE_ACCESS_KEY=your_porcupine_key
```

### Project Structure
```
grim/
├── Google_Grim_ObjDetect_ImageGen_ChatMode_News.py         # Core GRIM implementation
├── computer_vision.py                                      # Vision and image generation
├── GUI.py                                                  # User interface
├── logger.py                                               # Logging system
├── requirements.txt                                        # Dependencies
├── .env                                                    # API configuration
├── logs/                                                   # Log files
└── Images/                                                 # Generated images
```

### Usage Guide

1. **Starting the Application**
```bash
python Google_Grim_ObjDetect_ImageGen_ChatMode_News.py
```

2. **Voice Commands**
- Wake Word: "Hey Grim"
- Wait for "Listening..." indicator
- Speak commands clearly
- Example commands:
  - "What's the weather in [city]?"
  - "Show me the latest news"
  - "Generate an image of [description]"
  - "What's the stock price of [symbol]?"

3. **GUI Controls**
- Text Input: Type messages directly
- Voice Button: Toggle voice input
- Upload: Process local files
- Settings: Configure application parameters

### Error Handling

1. **Common Issues and Solutions**
- **No audio input:**
  - Check microphone permissions
  - Verify audio device selection
  - Restart application

- **Vision system errors:**
  - Update GPU drivers
  - Check CUDA installation
  - Verify camera permissions

- **API errors:**
  - Validate API keys
  - Check internet connection
  - Verify API service status

2. **Log Files**
- Located in `logs/` directory
- Format: `grim_log_YYYYMMDD_HHMMSS.json`
- Contains: conversations, system events, errors

### Security Notes

1. **API Key Protection**
- Store keys in `.env` file
- Never commit API keys to version control
- Regularly rotate API keys

2. **Data Privacy**
- Conversations logged locally only
- No cloud storage of user data
- Optional logging configuration

### Development Notes

1. **GPU Optimization**
- CUDA optimization for GTX 1650
- Memory-efficient attention for Stable Diffusion
- Configurable inference parameters

2. **Code Style**
- PEP 8 compliance
- Type hints used throughout
- Comprehensive error handling
- Modular architecture

### Team Members (404_found)

- Arrush Tandon
- Harshit Verma
- Divyansh Malani

### License
Copyright © 2024 404_found. All rights reserved.

### Acknowledgments
- CustomTkinter for GUI components
- YOLOv8 for object detection
- MediaPipe for face detection
- Stable Diffusion for image generation