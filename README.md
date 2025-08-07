<div align="center">

# LiveKit Shopping List Voice Assistant
#### **Voice-Enabled Shopping List Assistant with LiveKit Agents**

---

### 👨‍💻 Author
**Ivan Yang Rodriguez Carranza**

[![Email](https://img.shields.io/badge/Email-D14836?style=for-the-badge&logo=gmail&logoColor=white)](mailto:ivanrodcar@outlook.com)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/irodcar)
[![GitHub](https://img.shields.io/badge/GitHub-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/rodcar)

</div>

---

## 📋 Table of Contents
- [🎯 Overview](#-overview)
- [🎬 Demo](#-demo)
- [🚀 How to Use](#-how-to-use)
- [📝 License](#-license)

---

## 🎯 Overview

A voice-enabled shopping list assistant built with LiveKit that lets you manage your shopping list through natural voice commands. Add items, review your list, and send it via email - all hands-free.

---

## 🎬 Demo

<div align="center">



https://github.com/user-attachments/assets/77053dfa-b108-4718-a071-4fd6fb726d07



</div>

---

## 🚀 How to Use

### **Prerequisites**
- Python 3.12 or higher
- LiveKit account and credentials
- Azure Communication Services (for email functionality)
- OpenAI API key
- Deepgram API key (for speech-to-text)
- Cartesia API key (for text-to-speech)

### **Installation**

1. **Clone the repository:**
```bash
git clone https://github.com/rodcar/livekit-shopping-list-voice-assistant.git
cd livekit-shopping-list-voice-assistant
```

2. **Set up environment:**
```bash
uv venv
source .venv/bin/activate
uv sync
cp .env.example .env # Create .env file
```

3. **Configure environment variables:**
Create a `.env` file with the following variables:
```bash
# LiveKit Configuration
LIVEKIT_URL=your_livekit_url
LIVEKIT_API_KEY=your_livekit_api_key
LIVEKIT_API_SECRET=your_livekit_api_secret

# Speech-to-Text (Deepgram)
STT_MODEL=nova-2
STT_LANGUAGE=en-US

# Language Model (OpenAI)
LLM_MODEL=gpt-4o-mini

# Text-to-Speech (Cartesia)
TTS_MODEL=cartesia-tts
TTS_VOICE=your_preferred_voice
TTS_LANGUAGE=en-US

# Email Configuration (Azure Communication Services)
AZURE_COMMUNICATION_EMAIL_CONNECTION_STRING=your_acs_connection_string
AZURE_COMMUNICATION_EMAIL_SENDER=your_verified_sender_email
RECIPIENT_EMAIL=recipient@example.com
```

4. **Download required files:**
```bash
python agent.py download-files
```

5. **Run the voice assistant:**
```bash
python agent.py console
```

---

## 📝 License

This project is licensed under the [Apache License 2.0](LICENSE).

---

[Report Bug](https://github.com/rodcar/livekit-shopping-list-voice-assistant/issues) · [Request Feature](https://github.com/rodcar/livekit-shopping-list-voice-assistant/issues)
