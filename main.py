import os
import re
import json
import mimetypes
import urllib.parse
import magic
from pathlib import Path
from urllib.parse import urljoin, urlparse
from fastapi import FastAPI, Request, Form, HTTPException, Response
from fastapi.responses import HTMLResponse, FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from bs4 import BeautifulSoup
import requests
import aiohttp
import zipfile
import io
from datetime import datetime
from dotenv import load_dotenv
from typing import Optional, List, Dict, Any, Tuple
import tempfile

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

def is_valid_url(url: str) -> bool:
    """Check if a URL is valid"""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False

def get_base_url(url: str) -> str:
    """Get the base URL from a given URL"""
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"

def get_absolute_url(base_url: str, url: str) -> str:
    """Convert relative URL to absolute URL"""
    if not url:
        return ""
    if url.startswith(('http://', 'https://')):
        return url
    if url.startswith('//'):
        return f"{urlparse(base_url).scheme}:{url}"
    if url.startswith('/'):
        base = get_base_url(base_url)
        return f"{base}{url}"
    return f"{base_url.rstrip('/')}/{url.lstrip('/')}"

def get_file_extension(content_type: str) -> str:
    """Get file extension from content type"""
    if not content_type:
        return '.bin'
    
    ext = mimetypes.guess_extension(content_type)
    if not ext:
        # Common content types that might be missing
        if 'javascript' in content_type:
            return '.js'
        elif 'css' in content_type:
            return '.css'
        elif 'html' in content_type:
            return '.html'
        return '.bin'
    return ext

def scrape_website(url: str, selector: Optional[str] = None, scrape_type: str = 'text') -> dict:
    """Scrape content from a website
    
    Args:
        url: The URL to scrape
        selector: CSS selector (optional)
        scrape_type: Type of content to scrape ('text', 'links', 'images', 'videos')
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        base_url = get_base_url(url)
        
        if scrape_type == 'text':
            if selector:
                elements = soup.select(selector)
                content = '\n\n'.join([str(el) for el in elements])
            else:
                # Remove script and style elements
                for script in soup(["script", "style", "nav", "footer", "header"]):
                    script.decompose()
                content = soup.get_text(separator='\n', strip=True)
            return {"success": True, "content": content, "type": "text"}
            
        elif scrape_type == 'links':
            links = []
            for a in soup.find_all('a', href=True):
                href = a['href'].strip()
                if not href or href.startswith(('javascript:', 'mailto:', 'tel:', '#')):
                    continue
                
                absolute_url = get_absolute_url(base_url, href)
                if is_valid_url(absolute_url):
                    links.append({
                        'url': absolute_url,
                        'text': a.get_text(strip=True) or 'No text',
                        'external': not absolute_url.startswith(base_url)
                    })
            return {"success": True, "content": links, "type": "links"}
            
        elif scrape_type == 'images':
            images = []
            for img in soup.find_all('img', src=True):
                src = img['src'].strip()
                if not src:
                    continue
                    
                absolute_url = get_absolute_url(base_url, src)
                if is_valid_url(absolute_url):
                    images.append({
                        'url': absolute_url,
                        'alt': img.get('alt', 'No alt text'),
                        'title': img.get('title', '')
                    })
            return {"success": True, "content": images, "type": "images"}
            
        elif scrape_type == 'videos':
            videos = []
            # Check for video tags
            for video in soup.find_all('video'):
                src = video.get('src', '').strip()
                if not src and video.find('source'):
                    src = video.find('source').get('src', '').strip()
                
                if src:
                    absolute_url = get_absolute_url(base_url, src)
                    if is_valid_url(absolute_url):
                        videos.append({
                            'url': absolute_url,
                            'type': 'video',
                            'source': 'video_tag'
                        })
            
            # Check for iframe embeds (YouTube, Vimeo, etc.)
            for iframe in soup.find_all('iframe', src=True):
                src = iframe['src'].strip()
                if 'youtube.com/embed/' in src or 'youtu.be/' in src:
                    videos.append({
                        'url': src,
                        'type': 'youtube',
                        'source': 'iframe'
                    })
                elif 'vimeo.com/video/' in src:
                    videos.append({
                        'url': src,
                        'type': 'vimeo',
                        'source': 'iframe'
                    })
                else:
                    absolute_url = get_absolute_url(base_url, src)
                    if is_valid_url(absolute_url):
                        videos.append({
                            'url': absolute_url,
                            'type': 'video',
                            'source': 'iframe'
                        })
            
            return {"success": True, "content": videos, "type": "videos"}
            
        else:
            return {"success": False, "error": f"Invalid scrape type: {scrape_type}"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/scrape")
async def scrape_website_endpoint(
    request: Request,
    url: str = Form(...),
    selector: str = Form(""),
    scrape_type: str = Form("text"),
    prompt: str = Form("Summarize the main points and provide key insights:")
):
    """Handle the scraping request with different content types"""
    # Scrape the website
    scrape_result = scrape_website(url, selector if selector else None, scrape_type)
    
    if not scrape_result["success"]:
        return {"success": False, "error": f"Scraping failed: {scrape_result['error']}"}
    
    # If it's a text scrape, analyze with DeepSeek
    analysis = None
    if scrape_type == 'text' and prompt:
        try:
            analysis = await analyze_with_deepseek(scrape_result["content"], prompt)
        except Exception as e:
            return {"success": False, "error": f"AI analysis failed: {str(e)}"}
    
    return {
        "success": True,
        "content": scrape_result["content"],
        "type": scrape_result["type"],
        "analysis": analysis
    }

@app.post("/download")
async def download_content(
    urls: List[str],
    content_type: str
):
    """Download multiple files as a zip"""
    if not urls:
        raise HTTPException(status_code=400, detail="No URLs provided")
    
    # Create a temporary file to store the zip
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
    
    try:
        with zipfile.ZipFile(temp_file.name, 'w') as zipf:
            for i, url in enumerate(urls):
                try:
                    response = requests.get(url, stream=True, timeout=10)
                    response.raise_for_status()
                    
                    # Get content type and extension
                    content_type = response.headers.get('content-type', '')
                    ext = get_file_extension(content_type)
                    
                    # Create a safe filename
                    filename = f"file_{i+1}{ext}"
                    
                    # Add file to zip
                    zipf.writestr(filename, response.content)
                except Exception as e:
                    print(f"Failed to download {url}: {str(e)}")
                    continue
        
        # Return the zip file
        return FileResponse(
            temp_file.name,
            media_type='application/zip',
            filename=f"scraped_{content_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create download: {str(e)}")
    finally:
        # Clean up the temporary file after sending
        try:
            os.unlink(temp_file.name)
        except:
            pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
