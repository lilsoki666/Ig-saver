from __future__ import annotations

import asyncio
import os
import re
import tempfile
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import yt_dlp
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, HttpUrl


APP_VERSION = "1.0.0"

app = FastAPI(title="IGSaver API", version=APP_VERSION)

# The mobile app talks directly to this API. Keep CORS open for this small public API.
# If you later put the backend behind your own domain, restrict allow_origins.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class FetchRequest(BaseModel):
    url: HttpUrl


class MediaInfo(BaseModel):
    ok: bool
    type: str
    title: str = ""
    caption: str = ""
    author: str = ""
    media_url: str = ""
    thumbnail_url: str = ""
    duration: float | None = None
    message: str = ""


def validate_instagram_url(url: str) -> None:
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    if host not in {"instagram.com", "www.instagram.com", "m.instagram.com"}:
        raise HTTPException(
            status_code=400,
            detail="URL harus berasal dari instagram.com.",
        )


def clean_caption(info: dict[str, Any]) -> str:
    for key in ("description", "comment_count", "title"):
        value = info.get(key)
        if key == "description" and isinstance(value, str) and value.strip():
            return value.strip()

    # yt-dlp sometimes exposes Instagram caption-like text in description.
    for key in ("caption",):
        value = info.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    return ""


def choose_format(info: dict[str, Any]) -> tuple[str, str, str]:
    """Return (type, media_url, thumbnail_url)."""
    thumbnail = info.get("thumbnail") or ""

    # Prefer direct video URL when the extractor gives one.
    if info.get("url") and info.get("vcodec") not in (None, "none"):
        return "video", info["url"], thumbnail

    # Some extractors return formats instead of a top-level URL.
    formats = info.get("formats") or []
    video_formats = [
        f for f in formats
        if f.get("url")
        and f.get("vcodec") not in (None, "none")
    ]
    if video_formats:
        video_formats.sort(
            key=lambda f: (
                f.get("height") or 0,
                f.get("tbr") or 0,
            ),
            reverse=True,
        )
        return "video", video_formats[0]["url"], thumbnail

    # Image-only public post.
    if info.get("url"):
        return "image", info["url"], thumbnail

    return "", "", thumbnail


def extract_sync(url: str) -> MediaInfo:
    validate_instagram_url(url)

    opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "noplaylist": True,
        "extract_flat": False,
        # Keep the extractor focused on public content. No cookie/session ID.
    }

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)

        if not isinstance(info, dict):
            raise RuntimeError("Extractor tidak mengembalikan metadata.")

        # Instagram carousels may appear as entries.
        entries = info.get("entries")
        if entries:
            entries = [e for e in entries if isinstance(e, dict)]
            if not entries:
                raise RuntimeError("Posting tidak memiliki media yang dapat dibaca.")
            first = entries[0]
            # Fill missing top-level fields from the first entry.
            for key in ("url", "thumbnail", "description", "title", "uploader"):
                if not info.get(key) and first.get(key):
                    info[key] = first[key]
            if not info.get("formats") and first.get("formats"):
                info["formats"] = first["formats"]

        media_type, media_url, thumbnail = choose_format(info)

        if not media_url:
            raise RuntimeError(
                "Posting ditemukan, tetapi URL media tidak tersedia dari sumber publik."
            )

        caption = clean_caption(info)
        author = (
            info.get("uploader")
            or info.get("channel")
            or info.get("creator")
            or ""
        )
        title = info.get("title") or ""

        return MediaInfo(
            ok=True,
            type=media_type,
            title=str(title),
            caption=caption,
            author=str(author),
            media_url=str(media_url),
            thumbnail_url=str(thumbnail),
            duration=info.get("duration"),
            message="Posting publik berhasil dibaca.",
        )

    except yt_dlp.utils.DownloadError as exc:
        text = str(exc)
        # Avoid returning an enormous internal traceback to the phone.
        if "login" in text.lower() or "private" in text.lower():
            message = (
                "Instagram meminta login atau posting tidak publik. "
                "IGSaver hanya mendukung posting publik tanpa login."
            )
        elif "403" in text:
            message = (
                "Instagram menolak permintaan otomatis (HTTP 403). "
                "Coba posting publik lain."
            )
        else:
            message = "Instagram tidak dapat dibaca saat ini. Coba lagi."
        raise RuntimeError(message) from exc


@app.get("/health")
async def health():
    return {"ok": True, "service": "IGSaver API", "version": APP_VERSION}


@app.post("/api/fetch", response_model=MediaInfo)
async def fetch_posting(payload: FetchRequest):
    try:
        result = await asyncio.to_thread(extract_sync, str(payload.url))
        return result
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc))


# Optional server-side download endpoint.
# The APK normally downloads media_url directly. This endpoint is useful when
# a media URL requires server-side HTTP headers in a future extractor update.
@app.get("/api/download")
async def download_media(url: str):
    if not url.startswith("https://"):
        raise HTTPException(status_code=400, detail="Hanya HTTPS yang diizinkan.")

    # Restrict this helper to URLs that came from Instagram/CDN-like hosts.
    host = (urlparse(url).hostname or "").lower()
    allowed = (
        "instagram.com" in host
        or "cdninstagram.com" in host
        or host.endswith("fbcdn.net")
    )
    if not allowed:
        raise HTTPException(status_code=400, detail="Host media tidak diizinkan.")

    import requests

    temp_dir = Path(tempfile.mkdtemp(prefix="igsaver-"))
    target = temp_dir / "media"

    try:
        r = requests.get(
            url,
            timeout=45,
            stream=True,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        r.raise_for_status()
        content_type = r.headers.get("content-type", "")
        if "video" in content_type:
            target = target.with_suffix(".mp4")
        else:
            target = target.with_suffix(".jpg")

        with target.open("wb") as f:
            for chunk in r.iter_content(1024 * 256):
                if chunk:
                    f.write(chunk)

        return FileResponse(
            target,
            media_type=content_type or "application/octet-stream",
            filename=target.name,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Gagal mengunduh media: {exc}")
