📰 TrueScan – AI News Journalist

### *AI-powered real-time news aggregation, summarization, and audio generation system*

---

## 🚀 Overview

**TrueScan** is an AI-driven news journalist that automatically:
✔ Fetches real-time news and Reddit discussions
✔ Summarizes the content using advanced LLMs
✔ Converts the summaries into natural audio
✔ Displays everything through a simple and accessible Streamlit interface

The project aims to reduce information overload and help visually impaired or busy users consume information effortlessly.

---

## ❓ Problem Statement

In today’s digital world, people are overloaded with information scattered across multiple platforms.
Reading, comparing, and verifying news is **time-consuming**, especially for:

* Visually impaired users
* Busy learners/professionals
* Users who prefer audio format

**TrueScan aims to solve this with automated retrieval, summarization, and audio generation.**

---

## ✅ Solution

TrueScan uses **Generative AI + Web Scraping + Text-to-Speech** to deliver news summaries in both text and audio formats.

---

## 🔹 Features

### 🔍 Real-time Retrieval

Fetches fresh news & Reddit discussions using **Bright Data MCP**.

### ✨ AI Summaries

Creates concise, context-aware summaries using **Gemini Flash (LLM)**.

### 🔊 Text-to-Speech

Generates natural-sounding audio using **ElevenLabs API**.

### 🖥️ User-Friendly UI

A clean, accessible **Streamlit** interface for all users.

### 🤖 Agentic Automation

Uses **LangChain + LangGraph** for smart decision making and workflow control.

---

## 🛠️ Tech Stack

### 🖥️ Frontend

* Streamlit

### ⚙️ Backend

* FastAPI

### 🤖 AI & ML

* LangChain
* LangGraph
* Gemini Flash (LLM)

### 🌐 Data Extraction

* Bright Data MCP

### 🔊 Audio Generation

* ElevenLabs TTS API

### 📦 Environment & Versioning

* Pipenv
* Git & GitHub

---

## 📌 System Architecture

```
User Input → Streamlit UI → FastAPI Backend
        ↓
LangChain + LangGraph Agents
        ↓
Bright Data MCP (News + Reddit)
        ↓
Gemini Flash (Summarization)
        ↓
ElevenLabs API (Audio Generation)
        ↓
Streamlit Output (Text + Audio)
```

---

## 📈 Outcomes

* Fully automated end-to-end news processing pipeline
* Real-time retrieval and summarization
* High-quality, natural audio output
* Accessible interface for visually impaired and busy users

---

## 🚀 Future Enhancements

* 🎤 Voice-based input
* 🌐 Multilingual summaries & audio (Hindi, Marathi, Tamil, etc.)
* 🔎 Personalized news recommendations
* 📱 Mobile app integration
* 📥 Offline downloadable daily briefings
* 🎭 Emotion-aware expressive text-to-speech

---

## 📁 Project Setup

### 1️⃣ Clone the Repository

```
git clone https://github.com/Atharva080324/TrueScan.git
cd your-repo-name
```

### 2️⃣ Install Dependencies

```
pipenv install
pipenv shell
```

### 3️⃣ Set Environment Variables

Create a `.env` file:

```
GEMINI_API_KEY=your_key
ELEVENLABS_API_KEY=your_key
BRIGHTDATA_API_KEY=your_key
```

### 4️⃣ Run FastAPI Backend

```
uvicorn app:app --reload
```

### 5️⃣ Run Streamlit Frontend

```
streamlit run main.py
```

---

## 🤝 Contributors

👤 **Atharva Deshmukh**

## ⭐ Show Your Support

If you like this project, consider giving it a **star ⭐ on GitHub**!

---

If you want, I can also make a **fancier README with badges, screenshots, GIF demo, or architecture diagram**.
