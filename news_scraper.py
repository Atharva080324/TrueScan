from utils import *
from aiolimiter import AsyncLimiter
from dotenv import load_dotenv
import os
from typing import Dict, List
import asyncio

load_dotenv()

class NewsScraper:
    __rate__limiter = AsyncLimiter(5,1)  # 5 requests per second  

    async def scrape_news(self,topics:List[str]) -> Dict[str,str]:
        results = {}

        for topic in topics:
            async with self.__rate__limiter:
                try:
                    # FIXED: pass topic (string), not [topic]
                    url = generate_valid_news_url(topic)
                    print("Generated URL:", url)

                    search_html = scrape_with_brightdata(url)
                    print(f"Scraped HTML for {topic}:", search_html[:500])

                    clean_text = clean_html_to_text(search_html)
                    headlines = extract_headlines(clean_text)
                    print(f"Extracted Headlines for {topic}:", headlines[:5])

                    summary = summarize_with_mistral_news_script(headlines=headlines)
                    print(f"Summary for {topic}:", summary)

                    results[topic] = summary

                except Exception as e:
                    print(f"Error fetching news for {topic}: {e}")  # <— show it!
                    results[topic] = f"Error fetching news for '{topic}': {str(e)}"

                await asyncio.sleep(1)  # small delay for rate limits

        return {"news_analysis": results}
