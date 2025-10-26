from fastapi import FastAPI, HTTPException, File, Response
from fastapi.responses import FileResponse
import os
from pathlib import Path
from dotenv import load_dotenv
import traceback
from models import NewsRequest
from utils import generate_broadcast_news, text_to_audio_elevenlabs_sdk, tts_to_audio
from news_scraper import NewsScraper
from reddit_scrapper import scrape_reddit_topics

app = FastAPI()
load_dotenv()

from datetime import datetime

@app.get("/")
async def root():
    return {"status": "online", "message": "TrueScan API is running"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "huggingface": bool(os.getenv("HUGGINGFACEHUB_API_TOKEN")),
            "brightdata": bool(os.getenv("BRIGHTDATA_API_TOKEN")),
            "elevenlabs": bool(os.getenv("ELEVEN_API_KEY")),
            "reddit": bool(os.getenv("REDDIT_CLIENT_ID"))
        }
    }


@app.post("/generate-news-audio")
async def generate_news_audio(request: NewsRequest):
    try:
        results = {}
        
        if request.source_type in ["news", "both"]:
            news_scraper = NewsScraper()
            results["news"] = await news_scraper.scrape_news(request.topics)
        
        if request.source_type in ["reddit", "both"]:
            results["reddit"] = await scrape_reddit_topics(request.topics)

        news_data = results.get("news", {})
        reddit_data = results.get("reddit", {})
        
        # Fixed: Removed api_key parameter
        news_summary = generate_broadcast_news(
            news_data=news_data,
            reddit_data=reddit_data,
            topics=request.topics
        )

        # Use text_to_audio_elevenlabs_sdk or fallback to gTTS
        try:
            audio_path = text_to_audio_elevenlabs_sdk(
                text=news_summary,
                voice_id="JBFqnCBsd6RMkjVDRZzb",
                model_id="eleven_multilingual_v2",
                output_format="mp3_44100_128",
                output_dir="audio"
            )
        except (NotImplementedError, ValueError) as e:
            # Fallback to gTTS if ElevenLabs is not available
            print(f"ElevenLabs not available, using gTTS: {e}")
            audio_path = tts_to_audio(text=news_summary, language="en")

        if audio_path and Path(audio_path).exists():
            with open(audio_path, "rb") as f:
                audio_bytes = f.read()

            return Response(
                content=audio_bytes,
                media_type="audio/mpeg",
                headers={"Content-Disposition": "attachment; filename=news-summary.mp3"}
            )
        else:
            raise HTTPException(status_code=500, detail="Audio file generation failed")
    
    except Exception as e:
        print("ERROR in /generate-news-audio:", e)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)