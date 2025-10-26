from urllib.parse import quote_plus
import os
import requests
from bs4 import BeautifulSoup
from typing import List, Dict
from fastapi import HTTPException
from langchain_google_genai import ChatGoogleGenerativeAI 
from pathlib import Path
from gtts import gTTS
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

os.getenv("BRIGHTDATA_API_TOKEN")
os.getenv("WEB_UNLOCKER_ZONE")


# Get Google API key
google_api_key = os.getenv("GOOGLE_API_KEY")

# --------------------- Web Scraping Utilities ---------------------

def generate_valid_news_url(keyword: str) -> str:
    q = quote_plus(keyword)
    return f"https://news.google.com/search?q={q}&tbs=sbd:1"

def scrape_with_brightdata(url: str) -> str:
    headers = {
        "Authorization": f"Bearer {os.getenv('BRIGHTDATA_API_TOKEN')}",
        "Content-Type": "application/json"
    }

    payload = {
        "zone": os.getenv("WEB_UNLOCKER_ZONE"),
        "url": url,
        "format": "raw"
    }

    try:
        response = requests.post("https://api.brightdata.com/request", json=payload, headers=headers)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"BrightData scraping error: {str(e)}")

def clean_html_to_text(html_content: str) -> str:
    soup = BeautifulSoup(html_content, 'html.parser')
    return soup.get_text(separator='\n').strip()

def extract_headlines(cleaned_text: str) -> str:
    lines = [line.strip() for line in cleaned_text.split('\n') if line.strip()]
    headlines = []
    current_block = []

    for line in lines:
        if current_block:
            headlines.append(current_block[0])
            current_block = []
        else:
            current_block.append(line)
    if current_block:
        headlines.append(current_block[0])
    return "\n".join(headlines)

def fetch_news_articles(topics: List[str]) -> str:
    all_headlines = []
    for topic in topics:
        url = generate_valid_news_url(topic)
        raw_html = scrape_with_brightdata(url)
        cleaned_text = clean_html_to_text(raw_html)
        headlines = extract_headlines(cleaned_text)
        all_headlines.append(f"Topic: {topic}\n{headlines}\n")
    return "\n".join(all_headlines)

# --------------------- LLM Summarization Utilities ---------------------

def summarize_with_mistral_news_script(headlines: str) -> str:
    system_prompt = """
You are a professional news editor creating a broadcast-ready script.

Guidelines:
- Summarize the most important headlines
- Write in a conversational, engaging tone
- Use short, clear sentences suitable for audio
- No markdown, emojis, or special formatting
- Organize by topic naturally
- End with a brief conclusion
"""

    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=google_api_key,
            temperature=0.4,
            max_tokens=1000
        )

        # Construct the full prompt
        full_prompt = f"{system_prompt}\n\nHeadlines:\n{headlines}"
        
        # Direct invocation
        response = llm.invoke(full_prompt)
        return response.content.strip()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Google API error: {str(e)}")

def generate_broadcast_news(news_data: Dict, reddit_data: Dict, topics: List[str]) -> str:
    system_prompt = """
You are a professional virtual news reporter generating a natural-sounding audio news broadcast.

Guidelines:
- Write in a conversational, engaging tone suitable for audio
- Use short, clear sentences
- Avoid jargon and complex terms
- Include transitions between topics
- No markdown, emojis, or special formatting
- Write as if speaking directly to listeners
- Keep it concise but informative
- End with a friendly sign-off
"""

    try:
        topic_blocks = []
        for topic in topics:
            news_content = news_data.get("news_analysis", {}).get(topic, "")
            reddit_content = reddit_data.get("reddit_analysis", {}).get(topic, "")
            context = []
            if news_content:
                context.append(f"OFFICIAL NEWS CONTENT:\n{news_content}")
            if reddit_content:
                context.append(f"REDDIT DISCUSSION CONTENT:\n{reddit_content}")
            if context:
                topic_blocks.append(f"TOPIC: {topic}\n\n" + "\n\n".join(context))

        user_prompt = "\n\n--- NEW TOPIC ---\n\n".join(topic_blocks)

        llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=google_api_key,
            temperature=0.4,
            max_tokens=1000
        )

        # Construct the full prompt
        full_prompt = f"{system_prompt}\n\n{user_prompt}"
        
        # Direct invocation
        response = llm.invoke(full_prompt)
        return response.content.strip()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --------------------- TTS Utilities ---------------------

AUDIO_DIR = Path("audio")
AUDIO_DIR.mkdir(exist_ok=True)

def tts_to_audio(text: str, language: str = "en") -> str:
    """Convert text to speech using gTTS."""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = AUDIO_DIR / f"tts_{timestamp}.mp3"
        tts = gTTS(text=text, lang=language, slow=False)
        tts.save(str(filename))
        return str(filename)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"gTTS error: {str(e)}")

def text_to_audio_elevenlabs_sdk(text: str, voice_id: str="JBFqnCBsd6RMkjVDRZzb", 
                                  model_id: str="eleven_multilingual_v2", 
                                  output_format: str="mp3_44100_128",
                                  output_dir: str="audio",
                                  api_key: str=None) -> str:
    """Convert text to speech using ElevenLabs API."""
    api_key = api_key or os.getenv("ELEVEN_API_KEY")
    if not api_key:
        raise ValueError("ElevenLabs API key required")
    
    try:
        from elevenlabs import ElevenLabs
        
        client = ElevenLabs(api_key=api_key)
        audio_stream = client.text_to_speech.convert(
            text=text, 
            voice_id=voice_id, 
            model_id=model_id, 
            output_format=output_format
        )
        
        Path(output_dir).mkdir(exist_ok=True)
        filename = Path(output_dir) / f"tts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3"
        
        with open(filename, "wb") as f:
            for chunk in audio_stream:
                f.write(chunk)
        
        return str(filename)
        
    except ImportError:
        raise NotImplementedError("ElevenLabs SDK is not installed. Install it with: pip install elevenlabs")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ElevenLabs error: {str(e)}")