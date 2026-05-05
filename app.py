from flask import Flask, jsonify, request
import yt_dlp
import os

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({'status': 'Live Check Server Running'})

@app.route('/check')
def check():
    url = request.args.get('url', '')
    if not url:
        return jsonify({'live': False, 'error': 'No URL provided'})
    
    live_url = url.rstrip('/')
    if any(x in live_url for x in ['/@', '/channel/', '/c/', '/user/']) and not live_url.endswith('/live'):
        live_url = live_url + '/live'
    
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
        'noplaylist': True,
        'socket_timeout': 20,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(live_url, download=False)
            is_live = bool(info and (
                info.get('is_live') or
                info.get('live_status') == 'is_live'
            ))
            return jsonify({
                'live': is_live,
                'title': info.get('title', '') if info else '',
                'url': live_url
            })
    except Exception as e:
        return jsonify({'live': False, 'error': str(e)})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
