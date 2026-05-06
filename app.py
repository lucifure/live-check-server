from flask import Flask, jsonify, request
import requests
import os
import re

app = Flask(__name__)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Cache-Control': 'max-age=0',
}

def get_live_url(url):
    url = url.strip().rstrip('/')
    if re.search(r'youtube\.com/(@|channel/|c/|user/)', url) and not url.endswith('/live'):
        return url + '/live'
    return url

@app.route('/')
def home():
    return jsonify({'status': 'Live Check Server Running', 'version': '3.0'})

@app.route('/check')
def check():
    url = request.args.get('url', '')
    if not url:
        return jsonify({'live': False, 'error': 'No URL provided'})

    live_url = get_live_url(url)

    try:
        session = requests.Session()
        session.get('https://www.youtube.com', headers=HEADERS, timeout=10)
        res = session.get(live_url, headers=HEADERS, timeout=20)
        html = res.text

        checks = {
            'isLiveBroadcast': '"isLiveBroadcast"' in html,
            'isLiveTrue': '"isLive":true' in html,
            'live_playback': '"live_playback":1' in html,
            'hlsManifestUrl': 'hlsManifestUrl' in html,
            'isLiveContent': '"isLiveContent":true' in html,
            'watching_now': 'watching now' in html,
            'continuations_chat': '"continuations"' in html and 'chat' in html,
        }

        is_live = any(checks.values())

        return jsonify({
            'live': is_live,
            'url': live_url,
            'checks': checks,
            'html_length': len(html),
            'html_sample': html[1000:2000]
        })

    except Exception as e:
        return jsonify({'live': False, 'error': str(e)})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
