# youtube_transcript.py
# 유튜브 자막을 추출하는 Flask REST API 서버
# youtube-transcript-api 라이브러리 사용

from flask import Flask, request, jsonify
from youtube_transcript_api._api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound, VideoUnavailable
from urllib.parse import urlparse, parse_qs
import re

app = Flask(__name__)

# 유튜브 URL에서 video_id 추출 함수
# 예: https://youtu.be/xxxx 또는 https://www.youtube.com/watch?v=xxxx

def extract_video_id(url):
    # 짧은 URL
    match = re.match(r"https?://youtu.be/([\w-]+)", url)
    if match:
        return match.group(1)
    # 긴 URL
    parsed = urlparse(url)
    if parsed.hostname in ["www.youtube.com", "youtube.com"]:
        qs = parse_qs(parsed.query)
        return qs.get("v", [None])[0]
    return None

@app.route('/transcript', methods=['GET'])
def get_transcript():
    url = request.args.get('url')
    if not url:
        return jsonify({"error": "url 파라미터가 필요합니다."}), 400
    video_id = extract_video_id(url)
    if not video_id:
        return jsonify({"error": "유효하지 않은 유튜브 링크입니다."}), 400
    try:
        # 한글 자막 우선, 없으면 자동 감지
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        try:
            transcript = transcript_list.find_transcript(['ko'])
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