from typing import List, Dict
import os
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools
from dotenv import load_dotenv
from aiolimiter import AsyncLimiter
from datetime import datetime, timedelta
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent

# Load environment variables first
load_dotenv()

two_weeks_ago_str = (datetime.today() - timedelta(days=14)).strftime('%Y-%m-%d')
google_api_key = os.getenv("GOOGLE_API_KEY")
brightdata_token = os.getenv("BRIGHTDATA_API_TOKEN")

print("=" * 60)
print("🔧 Reddit Scraper Configuration")
print(f"Google API Key: {'✅ Found' if google_api_key else '❌ Missing'}")
print(f"BrightData Token: {'✅ Found' if brightdata_token else '❌ Missing'}")
print(f"Date filter: Posts after {two_weeks_ago_str}")
print("=" * 60)

server_params = StdioServerParameters(
    command="npx",
    env={"API_TOKEN": brightdata_token},
    args=["@brightdata/mcp"]
)

# Use Google Gemini Flash
model = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    google_api_key=google_api_key,
    temperature=0.4,
    max_tokens=1500
)

mcp_limiter = AsyncLimiter(1, 5)

class MCPOverloadedError(Exception):
    """Custom exception for MCP service overload"""
    pass


async def scrape_reddit_topics(topics: List[str]) -> Dict[str, Dict]:
    """Scrape and analyze Reddit topics using MCP tools."""
    print(f"\n🚀 Starting Reddit scraping for {len(topics)} topic(s)")
    
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                print("   📡 Initializing MCP session...")
                await session.initialize()
                
                print("   🔌 Loading MCP tools...")
                mcp_tools = await load_mcp_tools(session)
                print(f"   ✅ Loaded {len(mcp_tools)} MCP tools")
                
                # Print available tools for debugging
                for tool in mcp_tools[:3]:  # Show first 3 tools
                    print(f"      - {tool.name}")

                # Create agent using LangGraph with Google Gemini
                print("   🤖 Creating LangGraph agent...")
                agent = create_react_agent(
                    model=model,
                    tools=mcp_tools
                )
                print("   ✅ Agent created successfully")

                reddit_results = {}
                for i, topic in enumerate(topics, 1):
                    print(f"\n   [{i}/{len(topics)}] 🔍 Processing: {topic}")
                    try:
                        summary = await process_topic(agent, topic)
                        
                        # Check if summary is meaningful
                        if len(summary) < 50 or "unable" in summary.lower() or "error" in summary.lower():
                            print(f"   ⚠️  Warning: Short or error response for {topic}")
                            print(f"      Response preview: {summary[:100]}...")
                        else:
                            print(f"   ✅ Successfully processed: {topic} ({len(summary)} chars)")
                        
                        reddit_results[topic] = summary
                        
                        # Rate limiting between topics
                        if i < len(topics):
                            print(f"   ⏳ Waiting 5 seconds before next topic...")
                            await asyncio.sleep(5)
                            
                    except Exception as e:
                        print(f"   ❌ Error processing '{topic}': {str(e)}")
                        reddit_results[topic] = f"Unable to fetch Reddit discussions for {topic} due to technical issues."

                print(f"\n✅ Reddit scraping completed for all topics")
                return {"reddit_analysis": reddit_results}
                
    except Exception as e:
        print(f"\n❌ Critical error in scrape_reddit_topics: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Return fallback data
        return {
            "reddit_analysis": {
                topic: f"Reddit data temporarily unavailable for {topic}" 
                for topic in topics
            }
        }


async def process_topic(agent, topic: str) -> str:
    """Process a single topic with the agent."""
    async with mcp_limiter:
        prompt = f"""
You are a Reddit community analyst. Your task is to find and summarize Reddit discussions about '{topic}'.

IMPORTANT INSTRUCTIONS:
1. Use the available tools to search Reddit for posts about '{topic}' from the last 2 weeks
2. Look for posts with good engagement (upvotes, comments)
3. Read the actual post content and top comments
4. If you can't find recent posts, try searching more broadly or check related subreddits

Provide a natural, conversational summary that includes:
- What people are saying about {topic} on Reddit
- Main talking points and opinions
- Interesting insights or perspectives shared by users (paraphrase, no usernames)
- Overall community sentiment and tone
- Any emerging trends or debates

Write as if you're telling someone what you learned from reading Reddit. Be specific and reference actual discussion points you found. If you truly cannot find any discussions, explain what you searched for and why there might not be content available.

CRITICAL: Do NOT say "I'm unable to access" or similar phrases unless you've actually attempted to use the tools and failed. Make a genuine attempt to search and retrieve data first.
"""
        
        try:
            print(f"      🔄 Sending request to agent...")
            
            # Invoke the agent
            result = await agent.ainvoke({
                "messages": [{"role": "user", "content": prompt}]
            })
            
            print(f"      📨 Received response from agent")
            
            # Extract content from the response
            if isinstance(result, dict) and "messages" in result:
                messages = result["messages"]
                if messages:
                    last_message = messages[-1]
                    
                    # Try to get content from the message
                    if hasattr(last_message, "content"):
                        content = last_message.content
                    elif isinstance(last_message, dict) and "content" in last_message:
                        content = last_message["content"]
                    else:
                        content = str(last_message)
                    print(f"      ✅ REDDIT CONTENT FOR '{topic}':")
                    print(f"      {'='*50}")
                    print(f"      {content}...")  
                    print(f"      {'='*50}")
                    print(f"      Total length: {len(content)} characters")
                    if len(content) < 50:
                        print(f"      ⚠️  Short response: {content}")
                        return f"Limited Reddit discussion found for {topic}. The community may not have been actively discussing this topic recently."
                    
                    return content
            
            # Fallback
            print(f"      ⚠️  Unexpected result format")
            return f"Reddit discussions for {topic} could not be retrieved in the expected format."
            
        except Exception as e:
            error_msg = str(e)
            print(f"      ❌ Error in process_topic: {error_msg}")
            
            if "Overloaded" in error_msg or "429" in error_msg:
                raise MCPOverloadedError("Service overloaded")
            elif "rate limit" in error_msg.lower():
                return f"Rate limit reached while searching for {topic}. Please try again in a few minutes."
            else:
                return f"Technical issue while retrieving Reddit discussions for {topic}. This may be a temporary problem with the Reddit data service."