from __future__ import annotations

import json
import socket
import time
import urllib.parse
import urllib.request

from fastapi import APIRouter, HTTPException, Query, Request

router = APIRouter()


def _fetch_json(url: str, timeout: float = 8.0) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "UtilityHub/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # nosec B310
        return json.loads(resp.read().decode("utf-8", errors="ignore"))


@router.get('/ip-info')
async def ip_info(request: Request) -> dict:
    try:
        data = _fetch_json('https://ipapi.co/json/')
        return {
            'ip': data.get('ip') or request.client.host,
            'city': data.get('city'),
            'country': data.get('country_name'),
            'region': data.get('region'),
            'timezone': data.get('timezone'),
            'org': data.get('org'),
        }
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f'Unable to fetch IP info: {exc}') from exc


@router.get('/website-status')
async def website_status(url: str = Query(..., description='Website URL')) -> dict:
    parsed = urllib.parse.urlparse(url if '://' in url else f'https://{url}')
    if parsed.scheme not in {'http', 'https'} or not parsed.netloc:
        raise HTTPException(status_code=400, detail='Please provide a valid HTTP/HTTPS URL.')

    target = parsed.geturl()
    started = time.perf_counter()
    try:
        req = urllib.request.Request(target, method='HEAD', headers={"User-Agent": "UtilityHub/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:  # nosec B310
            elapsed = (time.perf_counter() - started) * 1000
            ip = socket.gethostbyname(parsed.netloc)
            return {
                'url': target,
                'status_code': getattr(resp, 'status', 200),
                'online': True,
                'response_ms': round(elapsed, 2),
                'ip': ip,
            }
    except Exception as exc:
        elapsed = (time.perf_counter() - started) * 1000
        return {
            'url': target,
            'status_code': None,
            'online': False,
            'response_ms': round(elapsed, 2),
            'error': str(exc),
        }
