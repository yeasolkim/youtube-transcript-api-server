# youtube_transcript.py
# 유튜브 자막을 추출하는 Flask REST API 서버
# youtube-transcript-api 라이브러리 사용

from flask import Flask, request, jsonify
from youtube_transcript_api._api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound, VideoUnavailable
from urllib.parse import urlparse, parse_qs
import re

app = Flask(__name__)

# 프록시 리스트 (주신 리스트 반영)
proxies = [
    'http://123.140.146.57:5031',
    'http://138.68.60.8:80',
    'http://3.109.62.30:717',
    'http://4.156.78.45:80',
    'http://72.10.160.91:18749',
    'http://123.140.146.2:5031',
    'http://43.216.214.221:4289',
    'http://205.198.65.77:80',
    'http://123.141.181.84:5031',
    'http://43.216.143.123:9008',
    'http://42.118.0.3:16000',
    'http://27.79.212.60:16000',
    'http://23.247.136.254:80'
]

# 유튜브 URL에서 video_id 추출 함수
def extract_video_id(url):
    # 짧은 URL
    match = re.match(r"https?://youtu.be/([\w-]+)", url)
    if match:
        return match.group(1)
    # 긴 URL
    parsed = urlparse(url)
    if parsed.hostname in ["www.youtube.com", "youtube.com"]:
        qs = parse_qs(parsed.query)
        v_list = qs.get("v", [None])
        return v_list[0] if v_list else None
    return None

@app.route('/transcript', methods=['GET'])
def get_transcript():
    url = request.args.get('url')
    print(f"DEBUG: url = {url} (type: {type(url)})")
    if not url or not isinstance(url, str):
        return jsonify({"error": "url 파라미터가 필요합니다."}), 400
    video_id = extract_video_id(url)
    print(f"DEBUG: video_id = {video_id} (type: {type(video_id)})")
    if not video_id or not isinstance(video_id, str):
        return jsonify({"error": "유효하지 않은 유튜브 링크입니다."}), 400
    try:
        # 한글 자막 우선, 없으면 자동 감지
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id, proxies=proxies)
        try:
            transcript = transcript_list.find_transcript(['ko', 'a.ko'])
        except NoTranscriptFound:
            transcript = transcript_list.find_transcript(['en', 'a.en'])
        transcript_data = transcript.fetch()
        # 자막 텍스트만 합치기 (FetchedTranscriptSnippet은 .text 속성만 사용)
        full_text = '\n'.join([item.text for item in transcript_data])
        return jsonify({"transcript": full_text})
    except TranscriptsDisabled:
        return jsonify({"error": "이 영상은 자막이 비활성화되어 있습니다."}), 400
    except VideoUnavailable:
        return jsonify({"error": "유효하지 않은 영상입니다."}), 400
    except Exception as e:
        return jsonify({"error": f"자막 추출 중 오류: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
