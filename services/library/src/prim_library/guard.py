"""Bounded per-process HTTP protection, not a substitute for edge quota enforcement."""
from __future__ import annotations
import hashlib
import secrets
import time
from starlette.responses import JSONResponse


class RequestGuard:
    def __init__(self, app, per_minute=120, max_clients=4096):
        self.app, self.limit, self.capacity = app, per_minute, max_clients
        self.salt = secrets.token_bytes(32)
        self.window = int(time.monotonic() // 60)
        self.counts = {}

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            return await self.app(scope, receive, send)
        window = int(time.monotonic() // 60)
        if window != self.window:
            self.counts.clear()
            self.window = window
        address = str(scope.get('client', ('unknown', 0))[0])
        key = hashlib.blake2b(address.encode(), key=self.salt, digest_size=16).digest()
        if key not in self.counts and len(self.counts) >= self.capacity:
            return await JSONResponse({'error': 'capacity_limit'}, status_code=429, headers={'Retry-After': '60'})(scope, receive, send)
        self.counts[key] = self.counts.get(key, 0) + 1
        if self.counts[key] > self.limit:
            return await JSONResponse({'error': 'rate_limit'}, status_code=429, headers={'Retry-After': '60'})(scope, receive, send)
        await self.app(scope, receive, send)
