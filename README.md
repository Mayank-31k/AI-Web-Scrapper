# AI-Powered Web Scraper

A web application that allows you to scrape websites and analyze the content using AI (DeepSeek).

## Features

- Scrape content from any public website
- Optionally use CSS selectors to target specific elements
- Analyze scraped content with DeepSeek AI
- Clean, responsive web interface
- Real-time results

## Prerequisites

- Python 3.7+
- pip (Python package manager)
- DeepSeek API key

## Setup

1. Clone this repository
2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the project root and add your DeepSeek API key:
   ```
   DEEPSEEK_API_KEY=your_deepseek_api_key_here
   ```

## Running the Application

1. Start the server:
   ```
   python main.py
   ```
2. Open your web browser and navigate to:
   ```
   http://localhost:8000
   ```

## Usage

1. Enter the URL of the website you want to scrape
2. (Optional) Add a CSS selector to target specific elements
3. (Optional) Customize the AI analysis prompt
4. Click "Scrape & Analyze"
5. View the AI analysis and raw content

## Project Structure

- `main.py`: Main FastAPI application
- `templates/index.html`: Web interface
- `static/`: Static files (CSS, JS, images)
- `.env`: Environment variables (API keys)
- `requirements.txt`: Python dependencies

## License

MIT
