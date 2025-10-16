# Universal Video Downloader

A web-based video downloader that supports multiple platforms including YouTube, TikTok, X (Twitter), Reddit, Facebook, and Instagram. Download videos in MP4 format or extract audio as MP3, with quality selection options.

## Features

- **Multi-platform Support**: YouTube, TikTok, X, Reddit, Facebook, Instagram
- **Format Options**: Download as video (MP4) or audio (MP3)
- **Quality Selection**: Choose from available quality options
- **User-friendly Interface**: Clean, modern web interface
- **Fast Downloads**: Powered by yt-dlp

## Prerequisites

- Python 3.8 or higher
- FFmpeg (required for audio conversion and merging formats)

### Installing FFmpeg

**Windows:**
1. Download FFmpeg from https://ffmpeg.org/download.html
2. Extract the zip file
3. Add the `bin` folder to your system PATH

**macOS:**
```bash
brew install ffmpeg
```

**Linux:**
```bash
sudo apt update
sudo apt install ffmpeg
```

## Installation

1. Clone or download this repository

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Start the Flask backend server:
```bash
python app.py
```

2. Open `index.html` in your web browser (or serve it with a local server)

3. Paste a video URL from any supported platform

4. Click "Get Formats" to see available quality options

5. Select your preferred format (Video/Audio) and quality

6. Click "Download" to start downloading

## Supported Platforms

- **YouTube**: Full support for all video formats and qualities
- **TikTok**: Video and audio downloads
- **X (Twitter)**: Video downloads from tweets
- **Reddit**: Video downloads from Reddit posts
- **Facebook**: Public video downloads
- **Instagram**: Reels, posts, and IGTV videos

## Project Structure

```
VideoDownloader/
├── app.py              # Flask backend API
├── index.html          # Frontend HTML
├── style.css           # Styling
├── script.js           # Frontend JavaScript
├── requirements.txt    # Python dependencies
├── downloads/          # Temporary download folder (auto-created)
└── README.md          # This file
```

## API Endpoints

### POST /api/formats
Get available formats for a video URL
```json
{
  "url": "video_url_here"
}
```

### POST /api/download
Download video/audio in specified format
```json
{
  "url": "video_url_here",
  "type": "video",  // or "audio"
  "format_id": "format_id_here"  // optional
}
```

## Troubleshooting

**Error: FFmpeg not found**
- Make sure FFmpeg is installed and in your system PATH

**Error: Download failed**
- Some platforms may have restrictions on certain videos
- Try a different video or check if the URL is correct
- Some private or age-restricted content may not be downloadable

**CORS errors**
- Make sure the Flask server is running on port 5000
- Check that the API_URL in script.js matches your server address

## Notes

- Downloaded files are temporarily stored in the `downloads` folder
- The application clears previous downloads before starting a new one
- Some platforms may have rate limits or anti-bot measures
- Always respect copyright and platform terms of service

## License

This project is for educational purposes only. Users are responsible for complying with the terms of service of the platforms they download from and respecting copyright laws.
