import os
import re
import tempfile
import json
import subprocess
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl

app = FastAPI(title="IGSaver API", version="1.3.0")

class FetchRequest(BaseModel):
    url: HttpUrl

def valid_instagram_url(url: str) -> bool:
    return bool(re.match(r"^https?://(www\.)?instagram\.com/(p|reel|tv)/", url))

@app.get("/health")
def health():
    return {"ok": True, "service": "IGSaver API", "version": "1.3.0"}

@app.post("/api/fetch")
def fetch_post(req: FetchRequest):
    url = str(req.url)
    if not valid_instagram_url(url):
        raise HTTPException(400, "URL harus berupa posting/reel Instagram.")

    with tempfile.TemporaryDirectory() as td:
        out = os.path.join(td, "%(id)s.%(ext)s")
        cmd = [
            "yt-dlp",
            "--dump-single-json",
            "--no-warnings",
            "--skip-download",
            "--no-playlist",
            "--no-check-certificates",
            "--output", out,
            url,
        ]
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
        if p.returncode != 0:
            err = (p.stderr or p.stdout or "Gagal mengambil posting.")[-1200:]
            raise HTTPException(502, "Backend gagal mengambil posting: " + err)

        try:
            info = json.loads(p.stdout)
        except Exception:
            raise HTTPException(502, "Respons extractor tidak valid.")

        caption = info.get("description") or info.get("title") or ""
        entries = info.get("entries")
        if entries:
            media = []
            for e in entries:
                if not e:
                    continue
                u = e.get("url")
                if u:
                    media.append({"url": u, "type": e.get("_type") or "media"})
            if not media and info.get("url"):
                media = [{"url": info["url"], "type": info.get("ext", "media")}]
        else:
            media = []
            if info.get("url"):
                media.append({"url": info["url"], "type": info.get("ext", "media")})

        if not media:
            raise HTTPException(404, "Posting ditemukan tetapi URL media tidak tersedia.")

        return {
            "ok": True,
            "id": info.get("id"),
            "caption": caption,
            "type": info.get("ext") or "post",
            "media": media,
        }
