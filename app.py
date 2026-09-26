import os, socket, subprocess, json, re
from flask import Flask, request, jsonify

app = Flask(__name__)

def run(cmd, timeout=60):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return {
            "ok": p.returncode == 0,
            "code": p.returncode,
            "stdout": p.stdout[-12000:],
            "stderr": p.stderr[-12000:]
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}

def classify(text):
    t = (text or "").lower()
    findings = []
    if "sign in to confirm you're not a bot" in t or "not a bot" in t:
        findings.append("YouTube bot/challenge response")
    if "http error 403" in t or "403" in t:
        findings.append("HTTP 403 / access restriction")
    if "http error 429" in t or "429" in t:
        findings.append("HTTP 429 / rate limiting")
    if "requested format is not available" in t:
        findings.append("Requested format unavailable")
    if "ffmpeg" in t and ("not found" in t or "not recognized" in t):
        findings.append("FFmpeg unavailable")
    if "cookie" in t:
        findings.append("Cookie/authentication related message")
    if "po token" in t or "pot" in t:
        findings.append("YouTube PO Token / client challenge related message")
    return findings

@app.get("/")
def index():
    return {
        "service": "YouTube Render Diagnostic",
        "usage": "/check?url=https://www.youtube.com/watch?v=VIDEO_ID"
    }

@app.get("/check")
def check():
    url = request.args.get("url", "").strip()
    if not url:
        return jsonify({"error": "Missing ?url=YouTube_URL"}), 400

    result = {"url": url, "checks": {}}

    # Public IP
    ip = run(["python", "-c",
              "import urllib.request; print(urllib.request.urlopen('https://api.ipify.org', timeout=10).read().decode())"])
    result["checks"]["public_ip"] = ip

    # DNS
    try:
        result["checks"]["dns"] = {
            "ok": True,
            "addresses": sorted({x[4][0] for x in socket.getaddrinfo("www.youtube.com", 443)})
        }
    except Exception as e:
        result["checks"]["dns"] = {"ok": False, "error": str(e)}

    # Basic HTTPS access
    curl = run(["curl", "-I", "-L", "--max-time", "20", "https://www.youtube.com"])
    result["checks"]["youtube_https"] = curl

    # yt-dlp version
    yv = run(["yt-dlp", "--version"])
    result["checks"]["yt_dlp_version"] = yv

    # FFmpeg version
    ff = run(["ffmpeg", "-version"], timeout=20)
    result["checks"]["ffmpeg"] = ff

    # Extract metadata/formats without downloading media
    info = run([
        "yt-dlp",
        "--no-warnings",
        "--skip-download",
        "--dump-single-json",
        "--no-playlist",
        url
    ], timeout=90)
    result["checks"]["video_info"] = info

    combined = "\n".join([
        str(info.get("stderr", "")),
        str(info.get("stdout", "")),
        str(curl.get("stderr", "")),
    ])
    result["diagnosis"] = classify(combined)

    if not result["diagnosis"]:
        if info.get("ok"):
            result["diagnosis"] = ["YouTube metadata extraction succeeded; download failure may be format, FFmpeg, storage, timeout, or application-code related."]
        else:
            result["diagnosis"] = ["No automatic diagnosis. Inspect video_info.stderr."]

    if info.get("ok"):
        try:
            data = json.loads(info["stdout"])
            result["video"] = {
                "id": data.get("id"),
                "title": data.get("title"),
                "duration": data.get("duration"),
                "formats_count": len(data.get("formats", [])),
                "audio_formats": [
                    {
                        "format_id": f.get("format_id"),
                        "ext": f.get("ext"),
                        "acodec": f.get("acodec"),
                        "vcodec": f.get("vcodec"),
                        "abr": f.get("abr")
                    }
                    for f in data.get("formats", [])
                    if f.get("acodec") != "none"
                ][-20:]
            }
        except Exception:
            pass

    return jsonify(result)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)
