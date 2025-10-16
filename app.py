from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import yt_dlp
import os
import json
from pathlib import Path
import time
import random
from pytubefix import YouTube
from pytubefix.cli import on_progress
import requests
from bs4 import BeautifulSoup

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

DOWNLOAD_FOLDER = 'downloads'
Path(DOWNLOAD_FOLDER).mkdir(exist_ok=True)

# Rate limiting
last_download_time = 0
MIN_DOWNLOAD_INTERVAL = 8  # 8 seconds between downloads - more conservative

def get_ydl_opts():
    """Get base yt-dlp options with anti-bot measures"""
    return {
        'quiet': False,  # Show output for debugging
        'no_warnings': False,
        'nocheckcertificate': True,
        'extractor_args': {
            'youtube': {
                'player_client': ['mediaconnect'],  # Try mediaconnect client
            }
        },
    }

def download_with_pytubefix(url, download_type, quality):
    """Download using pytubefix with WEB client"""
    try:
        print(f"Trying pytubefix with URL: {url}, quality: {quality}")

        # Try WEB client first (more reliable without PO tokens)
        try:
            yt = YouTube(
                url,
                client='WEB',
                use_oauth=False,
                allow_oauth_cache=False
            )
            print(f"Video title: {yt.title}")
            print(f"Available streams: {len(yt.streams)}")
        except Exception as e:
            print(f"WEB client failed: {e}, trying IOS...")
            # Fallback to IOS client
            yt = YouTube(
                url,
                client='IOS',
                use_oauth=False,
                allow_oauth_cache=False
            )
            print(f"Video title: {yt.title}")
            print(f"Available streams: {len(yt.streams)}")

        if download_type == 'audio':
            # Get best audio stream
            stream = yt.streams.filter(only_audio=True).order_by('abr').desc().first()
            if not stream:
                stream = yt.streams.get_audio_only()

            if stream:
                print(f"Selected audio stream: {stream}")
                filepath = stream.download(output_path=DOWNLOAD_FOLDER)

                # Verify download
                if filepath and os.path.exists(filepath) and os.path.getsize(filepath) > 1000:
                    print(f"Audio download successful: {filepath}")
                    return filepath
                else:
                    print(f"Audio download failed or file too small")
                    return None
        else:
            # Try progressive first (video + audio combined), filter by quality
            if quality:
                # Filter by resolution
                stream = yt.streams.filter(
                    progressive=True,
                    file_extension='mp4',
                    res=f'{quality}p'
                ).first()

                if not stream:
                    # Try to get closest quality
                    all_streams = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc()
                    for s in all_streams:
                        if s.resolution and int(s.resolution.replace('p', '')) <= quality:
                            stream = s
                            break
            else:
                # Get best available
                stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()

            if not stream:
                # No progressive streams (common for Shorts), get best adaptive
                print("No progressive streams, trying adaptive streams...")
                stream = yt.streams.filter(adaptive=True, file_extension='mp4', only_video=False).order_by('resolution').desc().first()

                if not stream:
                    # Fallback to any mp4 stream
                    stream = yt.streams.filter(file_extension='mp4').order_by('resolution').desc().first()

            if stream:
                print(f"Selected video stream: {stream}")

                # Check if this stream matches the requested quality
                if quality:
                    stream_quality = int(stream.resolution.replace('p', '')) if stream.resolution else 0
                    # If user wants higher quality than what's available in progressive, use yt-dlp
                    if quality > 360 and stream_quality <= 360:
                        print(f"User requested {quality}p but only {stream_quality}p progressive available, falling back to yt-dlp for adaptive streams")
                        return None

                filepath = stream.download(output_path=DOWNLOAD_FOLDER)

                # Verify download
                if filepath and os.path.exists(filepath) and os.path.getsize(filepath) > 1000:
                    print(f"Video download successful: {filepath} at {stream.resolution}")
                    return filepath
                else:
                    print(f"Video download failed or file too small")
                    return None

        print("No suitable stream found")
        return None

    except Exception as e:
        print(f"Pytubefix error: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

@app.route('/api/formats', methods=['POST'])
def get_formats():
    """Get available formats for a given URL"""
    try:
        data = request.get_json()
        url = data.get('url')

        if not url:
            return jsonify({'error': 'URL is required'}), 400

        ydl_opts = get_ydl_opts()

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

            common_qualities = {
                1080: 'Full HD (1080p)',
                720: 'HD (720p)',
                480: 'SD (480p)',
                360: 'Low (360p)',
                144: 'Very Low (144p)'
            }

            all_video_formats = []
            all_audio_formats = []

            if 'formats' in info:
                for f in info['formats']:
                    height = f.get('height')

                    if f.get('vcodec') != 'none' and height:
                        ext = f.get('ext', '')

                        if ext in ['mp4', 'webm', 'm4a']:
                            filesize = f.get('filesize') or f.get('filesize_approx', 0)

                            all_video_formats.append({
                                'format_id': f['format_id'],
                                'height': height,
                                'ext': ext,
                                'filesize': filesize,
                                'fps': f.get('fps', 30),
                                'has_audio': f.get('acodec') != 'none'
                            })

                    elif f.get('acodec') != 'none' and f.get('vcodec') == 'none':
                        abr = f.get('abr', 0)
                        if abr:
                            all_audio_formats.append({
                                'format_id': f['format_id'],
                                'abr': abr,
                                'ext': f.get('ext', 'mp3'),
                                'filesize': f.get('filesize') or f.get('filesize_approx', 0)
                            })

            video_formats = []
            seen_heights = set()

            all_video_formats.sort(key=lambda x: (x['height'], x['filesize']), reverse=True)

            for vf in all_video_formats:
                height = vf['height']
                if height in common_qualities and height not in seen_heights:
                    video_formats.append({
                        'format_id': vf['format_id'],
                        'quality': common_qualities[height],
                        'resolution': f"{height}p",
                        'ext': 'mp4',
                        'filesize': vf['filesize']
                    })
                    seen_heights.add(height)

            audio_formats = []
            target_bitrates = {96, 128, 256, 320}
            seen_bitrates = set()

            all_audio_formats.sort(key=lambda x: x['abr'], reverse=True)

            for af in all_audio_formats:
                abr = round(af['abr'])
                closest = min(target_bitrates, key=lambda x: abs(x - abr))

                if closest not in seen_bitrates and abs(closest - abr) < 30:
                    audio_formats.append({
                        'format_id': af['format_id'],
                        'quality': f'{closest}kbps',
                        'ext': 'mp3',
                        'filesize': af['filesize']
                    })
                    seen_bitrates.add(closest)

            if not video_formats and all_video_formats:
                best = all_video_formats[0]
                video_formats.append({
                    'format_id': best['format_id'],
                    'quality': f"{best['height']}p",
                    'resolution': f"{best['height']}p",
                    'ext': 'mp4',
                    'filesize': best['filesize']
                })

            if not audio_formats and all_audio_formats:
                best = all_audio_formats[0]
                audio_formats.append({
                    'format_id': best['format_id'],
                    'quality': f"{round(best['abr'])}kbps",
                    'ext': 'mp3',
                    'filesize': best['filesize']
                })

            return jsonify({
                'title': info.get('title', 'Unknown'),
                'thumbnail': info.get('thumbnail', ''),
                'duration': info.get('duration', 0),
                'video_formats': video_formats,
                'audio_formats': audio_formats
            })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/download', methods=['POST'])
def download_video():
    """Download video/audio with pytubefix first, yt-dlp fallback"""
    global last_download_time

    data = request.get_json()
    url = data.get('url')
    download_type = data.get('type', 'video')
    quality = data.get('quality')

    if not url:
        return jsonify({'error': 'URL is required'}), 400

    # Rate limiting - wait if needed
    current_time = time.time()
    time_since_last = current_time - last_download_time
    if time_since_last < MIN_DOWNLOAD_INTERVAL:
        wait_time = MIN_DOWNLOAD_INTERVAL - time_since_last
        print(f"Rate limiting: waiting {wait_time:.1f} seconds...")
        time.sleep(wait_time)

    last_download_time = time.time()

    # Clear previous downloads
    for file in os.listdir(DOWNLOAD_FOLDER):
        try:
            os.remove(os.path.join(DOWNLOAD_FOLDER, file))
        except:
            pass

    is_youtube = 'youtube.com' in url or 'youtu.be' in url

    # Try pytubefix first for YouTube VIDEO downloads only
    # For audio, use yt-dlp to ensure proper MP3 conversion with FFmpeg
    if is_youtube and download_type == 'video':
        print("=" * 50)
        print("ATTEMPTING PYTUBEFIX DOWNLOAD")
        print("=" * 50)

        filepath = download_with_pytubefix(url, download_type, quality)

        if filepath and os.path.exists(filepath) and os.path.getsize(filepath) > 1000:
            filename = os.path.basename(filepath)
            print(f"SUCCESS: Pytubefix downloaded {filename}")
            return send_file(
                filepath,
                as_attachment=True,
                download_name=filename
            )
        else:
            print("Pytubefix failed, falling back to yt-dlp...")

    # Fallback to yt-dlp
    print("=" * 50)
    print("ATTEMPTING YT-DLP DOWNLOAD")
    print("=" * 50)

    try:
        ydl_opts = get_ydl_opts()
        ydl_opts['outtmpl'] = os.path.join(DOWNLOAD_FOLDER, '%(title)s.%(ext)s')

        if download_type == 'audio':
            # Download best audio and convert to MP3
            ydl_opts['format'] = 'bestaudio/best'
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': str(quality) if quality else '192',
            }]
            # Ensure we keep video/audio files after processing
            ydl_opts['keepvideo'] = False
            print(f"yt-dlp audio format: bestaudio, will convert to MP3 at {quality}kbps")
        else:
            # Download video based on quality setting
            if quality:
                # Try to get the specific quality requested
                ydl_opts['format'] = f'bestvideo[height<={quality}][ext=mp4]+bestaudio[ext=m4a]/best[height<={quality}][ext=mp4]/best[ext=mp4]/best'
            else:
                # Default: best available
                ydl_opts['format'] = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'

            ydl_opts['merge_output_format'] = 'mp4'
            print(f"yt-dlp video format: height<={quality}p, will merge to MP4")

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

            downloaded_files = os.listdir(DOWNLOAD_FOLDER)
            if downloaded_files:
                files_with_time = [(f, os.path.getctime(os.path.join(DOWNLOAD_FOLDER, f))) for f in downloaded_files]
                files_with_time.sort(key=lambda x: x[1], reverse=True)
                filename = files_with_time[0][0]
                filepath = os.path.join(DOWNLOAD_FOLDER, filename)

                if os.path.getsize(filepath) > 0:
                    print(f"SUCCESS: yt-dlp downloaded {filename}")
                    return send_file(
                        filepath,
                        as_attachment=True,
                        download_name=filename
                    )

    except Exception as e:
        print(f"YT-DLP ERROR: {str(e)}")
        return jsonify({'error': f'Download failed: {str(e)}'}), 500

    return jsonify({'error': 'All download methods failed'}), 500

@app.route('/')
def index():
    """Serve the main page"""
    return send_file('index.html')

@app.route('/privacy')
def privacy():
    """Serve the privacy policy page"""
    return send_file('privacy.html')

@app.route('/terms')
def terms():
    """Serve the terms of use page"""
    return send_file('terms.html')

@app.route('/sitemap.xml')
def sitemap():
    """Serve sitemap for search engines"""
    response = send_file('sitemap.xml')
    response.headers['Content-Type'] = 'application/xml; charset=utf-8'
    return response

@app.route('/robots.txt')
def robots():
    """Serve robots.txt for search engines"""
    response = send_file('robots.txt')
    response.headers['Content-Type'] = 'text/plain'
    return response

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'ok'})

@app.route('/api/donations', methods=['GET'])
def get_donations():
    """Get current donation progress from Ko-fi"""
    try:
        # Try to fetch from Ko-fi page
        kofi_url = 'https://ko-fi.com/universalvideodownloader/goal?g=0'

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

        response = requests.get(kofi_url, headers=headers, timeout=5)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')

            # Try to find goal progress in the page
            # Ko-fi typically has progress data in their goal widget
            # Look for percentage or progress indicators

            # Try to find progress percentage
            progress_elements = soup.find_all(['div', 'span'], class_=lambda x: x and 'progress' in x.lower())

            for element in progress_elements:
                text = element.get_text().strip()
                if '%' in text:
                    # Extract percentage
                    percentage = int(''.join(filter(str.isdigit, text)))
                    if 0 <= percentage <= 100:
                        return jsonify({'percentage': percentage})

            # Try to find goal amounts
            amounts = soup.find_all(string=lambda text: text and '$' in str(text))
            for amount_text in amounts:
                # Look for patterns like "$150 / $500" or "$150 of $500"
                if '/' in amount_text or ' of ' in amount_text:
                    try:
                        parts = amount_text.replace('$', '').replace(',', '')
                        if '/' in parts:
                            current, goal = parts.split('/')
                        else:
                            current, goal = parts.split(' of ')

                        current = float(current.strip())
                        goal = float(goal.strip())

                        if goal > 0:
                            percentage = min(int((current / goal) * 100), 100)
                            return jsonify({'percentage': percentage})
                    except:
                        continue

        # Fallback to local file if Ko-fi fetch fails
        donations_file = os.path.join(os.path.dirname(__file__), 'donations.json')
        if os.path.exists(donations_file):
            with open(donations_file, 'r') as f:
                data = json.load(f)
                current = data.get('current', 0)
                goal = data.get('goal', 500)
                percentage = min(int((current / goal) * 100), 100) if goal > 0 else 0
                return jsonify({'percentage': percentage})

        return jsonify({'percentage': 0})

    except Exception as e:
        print(f"Error fetching donations: {e}")
        # Fallback to local file
        try:
            donations_file = os.path.join(os.path.dirname(__file__), 'donations.json')
            if os.path.exists(donations_file):
                with open(donations_file, 'r') as f:
                    data = json.load(f)
                    current = data.get('current', 0)
                    goal = data.get('goal', 500)
                    percentage = min(int((current / goal) * 100), 100) if goal > 0 else 0
                    return jsonify({'percentage': percentage})
        except:
            pass

        return jsonify({'percentage': 0})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=os.environ.get('DEBUG', 'False') == 'True', host='0.0.0.0', port=port)
