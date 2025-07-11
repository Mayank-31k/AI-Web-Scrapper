import os
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from bs4 import BeautifulSoup
import requests
import aiohttp
import json
from dotenv import load_dotenv
from typing import Optional

# Load environment variables
load_dotenv()

app = FastAPI(title="AI-Powered Web Scraper")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Get DeepSeek API key from environment variables
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
if not DEEPSEEK_API_KEY:
    raise ValueError("Please set DEEPSEEK_API_KEY in .env file")

DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"

async def analyze_with_deepseek(content: str, prompt: str) -> str:
    """Send content to DeepSeek API for analysis"""
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    
    system_prompt = """You are a helpful AI assistant that analyzes web content. 
    Provide a concise summary and key insights about the following content."""
    
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"{prompt}\n\nContent to analyze:\n{content[:15000]}"}
        ],
        "temperature": 0.7,
        "max_tokens": 1000
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(DEEPSEEK_API_URL, headers=headers, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise HTTPException(status_code=response.status, detail=f"DeepSeek API error: {error_text}")
                
                result = await response.json()
                return result["choices"][0]["message"]["content"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calling DeepSeek API: {str(e)}")

def scrape_website(url: str, selector: Optional[str] = None) -> dict:
    """Scrape content from a website"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        if selector:
            elements = soup.select(selector)
            content = '\n\n'.join([str(el) for el in elements])
        else:
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            content = soup.get_text(separator='\n', strip=True)
        
        return {"success": True, "content": content}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/scrape")
async def scrape_and_analyze(
    request: Request,
    url: str = Form(...),
    selector: str = Form(""),
    prompt: str = Form("Summarize the main points and provide key insights:")
):
    # Scrape the website
    scrape_result = scrape_website(url, selector if selector else None)
    
    if not scrape_result["success"]:
        return {"success": False, "error": f"Scraping failed: {scrape_result['error']}"}
    
    # Analyze with DeepSeek
    try:
        analysis = await analyze_with_deepseek(scrape_result["content"], prompt)
        return {
            "success": True,
            "content": scrape_result["content"],
            "analysis": analysis
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
