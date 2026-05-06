from flask import Flask, jsonify, request
import requests
import os
import re

app = Flask(__name__)

YOUTUBE_API_KEY = os.environ.get('YOUTUBE_API_KEY', 'AIzaSyDnAsBrxe_aFkUSpqkrFDczUw-PpLoEhuY')

def extract_channel_handle(url):
    url = url.strip().rstrip('/')
    # Extract @handle, channel ID, or custom URL
    patterns = [
        r'youtube\.com/@([^/?#]+)',
        r'youtube\.com/channel/([^/?#]+)',
        r'youtube\.com/c/([^/?#]+)',
        r'youtube\.com/user/([^/?#]+)',
    ]
    for p in patterns:
        m = re.search(p, url)
        if m:
            return m.group(0), m.group(1), p
    return None, None, None

def get_channel_id(handle):
    # Search for channel by handle
    try:
        res = requests.get(
            'https://www.googleapis.com/youtube/v3/search',
            params={
                'part': 'snippet',
                'q': handle,
                'type': 'channel',
                'key': YOUTUBE_API_KEY,
                'maxResults': 1,
            },
            timeout=10
        )
        data = res.json()
        if data.get('items'):
            return data['items'][0]['snippet']['channelId']
    except:
        pass
    return None

def get_channel_id_direct(url):
    # Try to get channel ID directly from URL
    m = re.search(r'youtube\.com/channel/(UC[^/?#]+)', url)
    if m:
        return m.group(1)
    return None

def check_channel_live(channel_id):
    # Use YouTube API to check if channel has active live stream
    try:
        res = requests.get(
            'https://www.googleapis.com/youtube/v3/search',
            params={
                'part': 'snippet',
                'channelId': channel_id,
                'eventType': 'live',
                'type': 'video',
                'key': YOUTUBE_API_KEY,
                'maxResults': 1,
            },
            timeout=10
        )
        data = res.json()
        items = data.get('items', [])
        if items:
            video_id = items[0]['id']['videoId']
            title = items[0]['snippet']['title']
            return True, video_id, title
        return False, None, None
    except Exception as e:
        return False, None, str(e)

@app.route('/')
def home():
    return jsonify({'status': 'Live Check Server Running', 'version': '4.0 - YouTube API'})

@app.route('/check')
def check():
    url = request.args.get('url', '')
    if not url:
        return jsonify({'live': False, 'error': 'No URL provided'})

    # Try to get channel ID directly first
    channel_id = get_channel_id_direct(url)

    # If not found, search by handle
    if not channel_id:
        m = re.search(r'youtube\.com/@([^/?#]+)', url)
        if m:
            handle = m.group(1)
            # Try channels API with forHandle
            try:
                res = requests.get(
                    'https://www.googleapis.com/youtube/v3/channels',
                    params={
                        'part': 'id',
                        'forHandle': handle,
                        'key': YOUTUBE_API_KEY,
                    },
                    timeout=10
                )
                data = res.json()
                if data.get('items'):
                    channel_id = data['items'][0]['id']
            except:
                pass

        # Fallback to search
        if not channel_id:
            m2 = re.search(r'youtube\.com/(?:@|c/|user/)([^/?#]+)', url)
            if m2:
                channel_id = get_channel_id(m2.group(1))

    if not channel_id:
        return jsonify({'live': False, 'error': 'Could not find channel ID', 'url': url})

    is_live, video_id, title = check_channel_live(channel_id)

    return jsonify({
        'live': is_live,
        'channel_id': channel_id,
        'video_id': video_id,
        'title': title,
        'url': url,
        'watch_url': f'https://youtube.com/watch?v={video_id}' if video_id else None
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
