"""Optional, text-only explanations of detector reports through Ollama Cloud."""
import json
import os
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


OLLAMA_CHAT_URL = 'https://ollama.com/api/chat'
DEFAULT_MODEL = 'gemma4:31b'
ENV_FILE = Path(__file__).resolve().parents[2] / '.env'


def load_local_env():
    """Read the two optional Ollama settings without overriding shell variables."""
    try:
        lines = ENV_FILE.read_text(encoding='utf-8').splitlines()
    except OSError:
        return
    allowed = {'OLLAMA_API_KEY', 'OLLAMA_MODEL'}
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if line.startswith('export '):
            line = line[7:].lstrip()
        key, separator, value = line.partition('=')
        key, value = key.strip(), value.strip()
        if not separator or key not in allowed or not value:
            continue
        if value[:1] in ('"', "'") and value[-1:] == value[:1]:
            value = value[1:-1]
        elif ' #' in value:
            value = value.split(' #', 1)[0].rstrip()
        if not os.environ.get(key, '').strip():
            os.environ[key] = value


class ExplanationError(Exception):
    pass


def configured():
    return bool(os.environ.get('OLLAMA_API_KEY', '').strip())


def explain(report):
    api_key = os.environ.get('OLLAMA_API_KEY', '').strip()
    if not api_key:
        raise ExplanationError('Ollama explanations are not configured')

    analysis = report.get('analysis') or {}
    coverage = report.get('coverage') or {}
    thresholds = report.get('thresholds') or {}
    facts = {
        'assessment': analysis.get('assessment'),
        'detector_available': analysis.get('detector_available'),
        'detector_reason': analysis.get('reason'),
        'score': analysis.get('score'),
        'low_threshold': thresholds.get('low_threshold'),
        'suspicious_threshold': thresholds.get('suspicious_threshold'),
        'requested_frames': coverage.get('requested_frames'),
        'analyzed_frames': coverage.get('analyzed_frames'),
        'analyzed_faces': coverage.get('analyzed_faces'),
        'rejected_faces': coverage.get('rejected_faces'),
    }
    body = json.dumps({
        'model': os.environ.get('OLLAMA_MODEL', DEFAULT_MODEL),
        'stream': False,
        'options': {'temperature': 0.2, 'num_predict': 240},
        'messages': [
            {
                'role': 'system',
                'content': (
                    'Explain the supplied video detector report in plain language. '
                    'Use only the supplied facts. Explain how frame coverage and the '
                    'score relate to the stated assessment and thresholds when possible. '
                    'Do not claim to know which visual features caused the score; this is '
                    'not feature attribution. Do not call the video real, fake, authentic, '
                    'or manipulated as a certainty. State that the detector is experimental '
                    'and its score is not a calibrated probability. Distinguish AI assessment '
                    'from cryptographic file integrity. Keep the explanation under 160 words.'
                ),
            },
            {'role': 'user', 'content': json.dumps(facts, separators=(',', ':'))},
        ],
    }).encode('utf-8')
    request = Request(
        OLLAMA_CHAT_URL,
        data=body,
        headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'},
        method='POST',
    )
    try:
        with urlopen(request, timeout=45) as response:
            result = json.loads(response.read(256_000))
        text = result['message']['content'].strip()
        if not text:
            raise ValueError('Empty explanation')
        return text
    except HTTPError as exc:
        messages = {
            400: 'AI explanation service rejected the request; check the configured model name',
            401: 'AI explanation service rejected the API key; check the root .env file',
            403: 'AI explanation service denied this request; check API key access',
            404: 'AI explanation service did not find the configured model; check OLLAMA_MODEL',
            429: 'AI explanation service rate or usage limit reached; try again later',
        }
        message = messages.get(exc.code, 'AI explanation service returned an HTTP error')
        raise ExplanationError(message) from exc
    except TimeoutError as exc:
        raise ExplanationError('AI explanation request timed out; try again') from exc
    except URLError as exc:
        raise ExplanationError('Could not connect to the AI explanation service; check your internet connection') from exc
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise ExplanationError('AI explanation service could not produce an explanation') from exc
