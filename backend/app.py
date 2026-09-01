import re
import json
import os
import tempfile
import subprocess

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl


app = FastAPI(
    title="IGSaver API",
    version="1.3.0"
)


class FetchRequest(BaseModel):

    url: HttpUrl


def valid_instagram_url(url):

    pattern = (
        r"^https?://"
        r"(www\.)?"
        r"instagram\.com/"
        r"(p|reel|tv)/"
    )

    return bool(
        re.match(
            pattern,
            url
        )
    )


@app.get("/health")
def health():

    return {
        "ok": True,
        "service": "IGSaver API",
        "version": "1.3.0"
    }


@app.post("/api/fetch")
def fetch_post(request: FetchRequest):

    url = str(request.url)

    if not valid_instagram_url(url):

        raise HTTPException(
            status_code=400,
            detail="URL Instagram tidak valid."
        )

    with tempfile.TemporaryDirectory() as temp:

        output = os.path.join(
            temp,
            "%(id)s.%(ext)s"
        )

        command = [
            "yt-dlp",

            "--dump-single-json",

            "--no-warnings",

            "--skip-download",

            "--no-playlist",

            "--output",
            output,

            url
        ]

        try:

            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=90
            )

        except subprocess.TimeoutExpired:

            raise HTTPException(
                status_code=504,
                detail="Server terlalu lama memproses posting."
            )

        if result.returncode != 0:

            error = (
                result.stderr
                or result.stdout
                or "Gagal mengambil posting."
            )

            raise HTTPException(
                status_code=502,
                detail=error[-1500:]
            )

        try:

            info = json.loads(
                result.stdout
            )

        except Exception:

            raise HTTPException(
                status_code=502,
                detail="Respons extractor tidak valid."
            )

        caption = (
            info.get("description")
            or info.get("title")
            or ""
        )

        media = []

        entries = info.get("entries")

        if entries:

            for entry in entries:

                if not entry:
                    continue

                media_url = entry.get(
                    "url"
                )

                if media_url:

                    media.append({
                        "url": media_url,
                        "type": entry.get(
                            "ext",
                            "media"
                        )
                    })

        else:

            media_url = info.get(
                "url"
            )

            if media_url:

                media.append({
                    "url": media_url,
                    "type": info.get(
                        "ext",
                        "media"
                    )
                })

        if not media:

            raise HTTPException(
                status_code=404,
                detail=(
                    "Posting ditemukan tetapi "
                    "URL media tidak tersedia."
                )
            )

        return {
            "ok": True,

            "id": info.get(
                "id"
            ),

            "caption": caption,

            "type": info.get(
                "ext",
                "post"
            ),

            "media": media
        }
