from flask import Flask, jsonify, request
import requests
import os
import re

app = Flask(__name__)

def get_live_url(url):
    url = url.strip().rstrip('/')
    if re.search(r'youtube\.com/(@|channel/|c/|user/)', url) and not url.endswith('/live'):
        return url + '/live'
    return url

@app.route('/')
def home():
    return jsonify({'status': 'Live Check Server Running', 'version': '2.0'})

@app.route('/check')
def check():
    url = request.args.get('url', '')
    if not url:
        return jsonify({'live': False, 'error': 'No URL provided'})

    live_url = get_live_url(url)

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Cache-Control': 'no-cache',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
    }

    try:
        session = requests.Session()
        # First visit YouTube homepage to get cookies
        session.get('https://www.youtube.com', headers=headers, timeout=10)

        # Now check the live URL
        res = session.get(live_url, headers=headers, timeout=20)
        html = res.text

        is_live = (
            '"isLiveBroadcast"' in html or
            '"isLive":true' in html or
            '"live_playback":1' in html or
            'hlsManifestUrl' in html or
            '"isLiveContent":true' in html or
            ('watching now' in html) or
            ('"continuations"' in html and 'chat' in html)
        )

        return jsonify({
            'live': is_live,
            'url': live_url,
            'status': res.status_code
        })

    except Exception as e:
        return jsonify({'live': False, 'error': str(e)})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
