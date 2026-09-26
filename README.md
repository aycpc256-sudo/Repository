# YouTube Render Diagnostic

Render 서버에서 YouTube 접근/yt-dlp/FFmpeg 문제를 진단하기 위한 최소한의 테스트 서버입니다.

## 1. GitHub

이 폴더 전체를 GitHub 저장소에 올립니다.

## 2. Render

Render에서 `New > Web Service`로 GitHub 저장소를 연결합니다.

- Build Command:
  `pip install -r requirements.txt && pip install -U yt-dlp`
- Start Command:
  `python app.py`

`render.yaml`을 사용하는 경우 설정이 자동으로 적용됩니다.

## 3. 테스트

배포 후:

`https://YOUR-RENDER-DOMAIN.onrender.com/check?url=YOUTUBE_URL`

예:

`/check?url=https://www.youtube.com/watch?v=VIDEO_ID`

## 확인 항목

- Render 공인 IP
- YouTube DNS
- YouTube HTTPS 응답
- yt-dlp 버전
- FFmpeg 설치 여부
- 해당 영상의 메타데이터/포맷 추출
- 403 / 429 / bot challenge / format / cookie / PO Token 관련 오류 분류

## 주의

이 프로젝트는 차단 우회 코드가 아니라 원인 진단용입니다.
`video_info.stderr`와 `diagnosis` 결과를 확인하면 다음 조치를 결정하기 쉽습니다.
