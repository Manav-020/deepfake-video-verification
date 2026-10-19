import hashlib
import hmac
import json
import re
import secrets
from pathlib import Path
from urllib.parse import urlparse
from fastapi import FastAPI, Request, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, Response, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.concurrency import run_in_threadpool
from starlette.middleware.trustedhost import TrustedHostMiddleware
from .config import ROOT, load_settings
from .crypto import digest, verify
from .detector import model_ready
from .service import Service

FRONTEND_DIST = ROOT.parent / 'frontend' / 'dist'


class BodyLimit:
    """Reject oversized/chunked requests before the multipart parser can spool them."""
    def __init__(self, app, limit):
        self.app, self.limit = app, limit

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            return await self.app(scope, receive, send)
        count = 0
        headers = dict(scope['headers'])
        try:
            declared = int(headers.get(b'content-length', b'0'))
        except ValueError:
            return await Response('Invalid content length', 400)(scope, receive, send)
        if declared > self.limit:
            return await Response('Upload exceeds configured size limit', 413)(scope, receive, send)

        async def bounded_receive():
            nonlocal count
            message = await receive()
            count += len(message.get('body', b''))
            if count > self.limit:
                raise HTTPException(413, 'Upload exceeds configured size limit')
            return message
        await self.app(scope, bounded_receive, send)


def create_app(runtime=None, settings=None, detector=None):
    settings = settings or load_settings()
    service = Service(Path(runtime or ROOT / 'runtime'), settings, detector)
    app = FastAPI(title='FrameSeal', docs_url=None, redoc_url=None)
    app.state.service = service
    app.add_middleware(BodyLimit, limit=settings.max_upload_mb * 1024 * 1024 + 1024 * 1024)
    hosts = ['127.0.0.1', 'localhost', '[::1]']
    if runtime is not None:
        hosts.append('testserver')  # Isolated TestClient instances only.
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=hosts)
    if (FRONTEND_DIST / 'assets').is_dir():
        app.mount('/assets', StaticFiles(directory=FRONTEND_DIST / 'assets'), name='frontend-assets')
    # Domain-separated secret derived from persistent private bytes; never sent to clients.
    from cryptography.hazmat.primitives import serialization
    secret = service.signer.key.private_bytes(serialization.Encoding.Raw,
                serialization.PrivateFormat.Raw, serialization.NoEncryption())

    def csrf(session):
        return hmac.new(secret, ('csrf:' + session).encode(), hashlib.sha256).hexdigest()

    def owner(request):
        token = request.cookies.get('frameseal_session', '')
        if not re.fullmatch('[a-f0-9]{64}', token):
            raise HTTPException(403, 'Open the home page to start a private session')
        return digest(token.encode())

    @app.middleware('http')
    async def protections(request, call_next):
        if request.method in ('POST', 'PUT', 'PATCH', 'DELETE'):
            session = request.cookies.get('frameseal_session', '')
            supplied = request.headers.get('x-csrf-token', '')
            origin = request.headers.get('origin')
            if origin and urlparse(origin).netloc != request.headers.get('host'):
                return JSONResponse({'detail': 'Cross-origin request rejected'}, status_code=403)
            if not session or not hmac.compare_digest(csrf(session), supplied):
                return JSONResponse({'detail': 'Invalid session/CSRF token; reload the page'}, status_code=403)
        response = await call_next(request)
        response.headers.update({'X-Content-Type-Options': 'nosniff', 'Referrer-Policy': 'no-referrer',
                                 'Cache-Control': 'no-store', 'X-Frame-Options': 'DENY',
                                 'Content-Security-Policy': "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; media-src 'self'; object-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"})
        return response

    @app.exception_handler(LookupError)
    async def missing(request, exc):
        return JSONResponse({'detail': 'Record not found or link revoked'}, status_code=404)

    @app.exception_handler(PermissionError)
    async def forbidden(request, exc):
        return JSONResponse({'detail': str(exc)}, status_code=403)

    @app.exception_handler(ValueError)
    async def invalid(request, exc):
        return JSONResponse({'detail': str(exc)}, status_code=400)

    @app.get('/', response_class=HTMLResponse)
    def home(request: Request):
        index = FRONTEND_DIST / 'index.html'
        if not index.is_file():
            return JSONResponse({'detail': 'Frontend is not built. Run the frontend development server or build it.'}, status_code=503)
        response = FileResponse(index)
        if not re.fullmatch('[a-f0-9]{64}', request.cookies.get('frameseal_session', '')):
            response.set_cookie('frameseal_session', secrets.token_hex(32), httponly=True,
                                samesite='strict', max_age=60 * 60 * 24 * 30)
        return response

    @app.get('/api/session')
    def session(request: Request, response: Response):
        token = request.cookies.get('frameseal_session', '')
        if not re.fullmatch('[a-f0-9]{64}', token):
            token = secrets.token_hex(32)
            response.set_cookie('frameseal_session', token, httponly=True,
                                samesite='strict', max_age=60 * 60 * 24 * 30)
        return {'csrf_token': csrf(token)}

    @app.get('/api/status')
    def status():
        ready, message = model_ready()
        return {'model_ready': ready, 'model_status': message, 'thresholds': 'Provisional / experimental',
                'dataset_evaluation': 'Not performed; supply legally obtained labeled videos',
                'max_upload_mb': settings.max_upload_mb,
                'max_duration_seconds': settings.max_duration_seconds,
                'signing_key_id': service.signer.key_id}

    async def read_upload(file, maximum):
        data = bytearray()
        try:
            while chunk := await file.read(1024 * 1024):
                data.extend(chunk)
                if len(data) > maximum:
                    raise HTTPException(413, 'File exceeds configured size limit')
        finally:
            await file.close()
        if not data:
            raise HTTPException(400, 'Empty file')
        return bytes(data)

    @app.post('/api/analyze')
    async def analyze(request: Request, video: UploadFile = File(...)):
        identity = owner(request)
        if not service.lock.acquire(blocking=False):
            raise HTTPException(429, 'Analysis already running; retry when it finishes')
        path = None
        committed = False
        try:
            data = await read_upload(video, settings.max_upload_mb * 1024 * 1024)
            identifier = secrets.token_hex(16)
            path = service.root / 'videos' / (identifier + '.bin')
            with path.open('xb') as f:
                f.write(data)
            result = await run_in_threadpool(service.finish, identifier, identity, path)
            committed = True
            return result
        finally:
            if path is not None and not committed:
                path.unlink(missing_ok=True)
            service.lock.release()

    @app.get('/api/reports')
    def history(request: Request):
        identity = owner(request)
        with service.db() as con:
            ids = [r[0] for r in con.execute('SELECT id FROM reports WHERE owner=? ORDER BY rowid DESC LIMIT 30', (identity,))]
        return [service.record(i, identity)[0] for i in ids]

    @app.get('/api/reports/{identifier}')
    def report(identifier: str, request: Request):
        report, envelope = service.record(identifier, owner(request))
        return {'report': report, 'envelope': envelope}

    @app.post('/api/reports/{identifier}/share')
    def share(identifier: str, request: Request):
        return {'url': '/s/' + service.share(identifier, owner(request))}

    @app.post('/api/reports/{identifier}/revoke')
    def revoke(identifier: str, request: Request):
        service.revoke(identifier, owner(request))
        return {'revoked': True}

    @app.get('/s/{token}', response_class=HTMLResponse)
    def shared_page(token: str):
        service.shared(token)
        # Tokens are generated by the server, but validate before HTML interpolation.
        if not re.fullmatch('[A-Za-z0-9_-]{43}', token):
            raise HTTPException(404)
        index = FRONTEND_DIST / 'index.html'
        if not index.is_file():
            return JSONResponse({'detail': 'Frontend is not built. Open this share from the frontend development server.'}, status_code=503)
        return FileResponse(index)

    @app.get('/s/{token}/video')
    def shared_video(token: str):
        _, _, data = service.shared(token)
        # Fixed generic type + nosniff prevents uploaded HTML being executed.
        return Response(data, media_type='video/mp4', headers={
            'Content-Disposition': 'inline; filename="analyzed-video.mp4"', 'Accept-Ranges': 'none'})

    @app.get('/s/{token}/report')
    def shared_report(token: str):
        _, envelope, _ = service.shared(token)
        return Response(json.dumps(envelope), media_type='application/json',
                        headers={'Content-Disposition': 'attachment; filename="signed-report.json"'})

    @app.post('/api/verify')
    async def verify_received(request: Request, video: UploadFile = File(...), report: UploadFile = File(...)):
        owner(request)
        report_bytes = await read_upload(report, 384_000)
        video_bytes = await read_upload(video, settings.max_upload_mb * 1024 * 1024)
        try:
            envelope = json.loads(report_bytes)
            return verify(envelope, video_bytes, service.signer.registry)
        except (ValueError, TypeError, KeyError, RecursionError) as exc:
            raise HTTPException(400, 'Malformed or unsupported signed report') from exc

    return app
