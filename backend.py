from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import FileResponse
import os
from pathlib import Path
from dotenv import load_dotenv
import traceback
from models import NewsRequest
from utils import generate_broadcast_news, text_to_audio_elevenlabs_sdk, tts_to_audio
from news_scraper import NewsScraper
from reddit_scrapper import scrape_reddit_topics
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or restrict later to ["http://127.0.0.1:5500"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

load_dotenv()

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
    """
    Original endpoint - returns audio file directly
    """
    try:
        results = {}
        
        if request.source_type in ["news", "both"]:
            news_scraper = NewsScraper()
            results["news"] = await news_scraper.scrape_news(request.topics)
        
        if request.source_type in ["reddit", "both"]:
            results["reddit"] = await scrape_reddit_topics(request.topics)

        news_data = results.get("news", {})
        reddit_data = results.get("reddit", {})
        
        # Generate the script
        news_summary = generate_broadcast_news(
            news_data=news_data,
            reddit_data=reddit_data,
            topics=request.topics
        )

        # Print script to console
        print("\n" + "="*70)
        print("📄 FINAL SCRIPT BEING SENT TO ELEVENLABS:")
        print("="*70)
        print(news_summary)
        print("="*70)
        print(f"Character count: {len(news_summary)}")
        print("="*70 + "\n")

        # Generate audio
        try:
            print("🔊 Generating audio with ElevenLabs...")
            audio_path = text_to_audio_elevenlabs_sdk(
                text=news_summary,
                voice_id="JBFqnCBsd6RMkjVDRZzb",
                model_id="eleven_multilingual_v2",
                output_format="mp3_44100_128",
                output_dir="audio"
            )
        except (NotImplementedError, ValueError) as e:
            print(f"⚠️ ElevenLabs not available, using gTTS: {e}")
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
        print("❌ ERROR in /generate-news-audio:", e)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate-news-audio-with-script")
async def generate_news_audio_with_script(request: NewsRequest):
    """
    Enhanced endpoint - returns both script text and audio information
    """
    try:
        results = {}
        
        if request.source_type in ["news", "both"]:
            news_scraper = NewsScraper()
            results["news"] = await news_scraper.scrape_news(request.topics)
        
        if request.source_type in ["reddit", "both"]:
            results["reddit"] = await scrape_reddit_topics(request.topics)

        news_data = results.get("news", {})
        reddit_data = results.get("reddit", {})
        
        # Generate the script
        news_summary = generate_broadcast_news(
            news_data=news_data,
            reddit_data=reddit_data,
            topics=request.topics
        )

        # Print script to console
        print("\n" + "="*70)
        print("📄 FINAL SCRIPT BEING SENT TO ELEVENLABS:")
        print("="*70)
        print(news_summary)
        print("="*70)
        print(f"Character count: {len(news_summary)}")
        print(f"Estimated credits needed: ~{len(news_summary) * 1.5:.0f}")
        print("="*70 + "\n")

        # Generate audio
        try:
            print("🔊 Generating audio with ElevenLabs...")
            audio_path = text_to_audio_elevenlabs_sdk(
                text=news_summary,
                voice_id="JBFqnCBsd6RMkjVDRZzb",
                model_id="eleven_multilingual_v2",
                output_format="mp3_44100_128",
                output_dir="audio"
            )
        except (NotImplementedError, ValueError) as e:
            print(f"⚠️ ElevenLabs not available, using gTTS: {e}")
            audio_path = tts_to_audio(text=news_summary, language="en")

        if not audio_path or not Path(audio_path).exists():
            raise HTTPException(status_code=500, detail="Audio file generation failed")

        # Get just the filename
        audio_filename = Path(audio_path).name

        # Return JSON with script and audio path
        return {
            "status": "success",
            "script": news_summary,
            "audio_filename": audio_filename,
            "character_count": len(news_summary),
            "topics": request.topics,
            "source_type": request.source_type,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        print("❌ ERROR in /generate-news-audio-with-script:", e)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/download-audio/{filename}")
async def download_audio(filename: str):
    """
    Download audio file by filename
    """
    try:
        # Security: Only allow files from audio directory
        audio_path = Path("audio") / filename
        
        # Prevent directory traversal
        if not audio_path.resolve().parent == Path("audio").resolve():
            raise HTTPException(status_code=403, detail="Access denied")
        
        if not audio_path.exists():
            raise HTTPException(status_code=404, detail="Audio file not found")
        
        return FileResponse(
            path=audio_path,
            media_type="audio/mpeg",
            filename="news-summary.mp3"
        )
    
    except Exception as e:
        print(f"❌ ERROR in /download-audio: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
