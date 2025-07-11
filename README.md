# Scrappy-AI

A web application that allows you to scrape websites, extract various types of content, and analyze it using AI (DeepSeek).

## Features

- **Multiple Scraping Modes**:
  - Text content extraction
  - Link extraction (internal/external)
  - Image extraction with previews
  - Video extraction (including YouTube and Vimeo embeds)
- AI-powered content analysis using DeepSeek
- Select and download multiple items
- Clean, responsive web interface
- Real-time results with loading indicators
- Option to use CSS selectors for precise content targeting

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

### Basic Text Scraping
1. Enter the website URL
2. Select "Text Content" as the scrape type
3. (Optional) Add a CSS selector to target specific elements
4. (Optional) Customize the AI analysis prompt
5. Click "Scrape & Analyze"
6. View the AI analysis and extracted text

### Extracting Links
1. Enter the website URL
2. Select "All Links" as the scrape type
3. Click "Scrape & Analyze"
4. View all links found on the page
5. Select specific links to download or click "Download All"

### Extracting Images
1. Enter the website URL
2. Select "Images" as the scrape type
3. Click "Scrape & Analyze"
4. Browse through the extracted images with previews
5. Select images to download or click "Download All"

### Extracting Videos
1. Enter the website URL
2. Select "Videos" as the scrape type
3. Click "Scrape & Analyze"
4. View embedded videos (YouTube, Vimeo, and direct video links)
5. Select videos to download or click "Download All"

### Downloading Content
- Check the checkboxes next to items you want to download
- Click the "Download (X)" button to download selected items
- Click "Download All" to download all items of the current type
- Files will be downloaded as a ZIP archive

## Project Structure

- `main.py`: Main FastAPI application
- `templates/index.html`: Web interface
- `static/`: Static files (CSS, JS, images)
- `.env`: Environment variables (API keys)
- `requirements.txt`: Python dependencies

## License

MIT
