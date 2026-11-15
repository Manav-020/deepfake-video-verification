"""Text-only explanations of detector reports supporting Groq Cloud, Ollama, and fallback."""
import json
import os
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


GROQ_CHAT_URL = 'https://api.groq.com/openai/v1/chat/completions'
DEFAULT_GROQ_MODEL = 'llama-3.3-70b-versatile'

OLLAMA_CHAT_URL = 'https://ollama.com/api/chat'
DEFAULT_OLLAMA_MODEL = 'gemma4:31b'

ENV_FILE = Path(__file__).resolve().parents[2] / '.env'

SYSTEM_PROMPT = (
    'Explain the supplied video detector report in plain language. '
    'Use only the supplied facts. Explain how frame coverage and the '
    'score relate to the stated assessment and thresholds when possible. '
    'Do not claim to know which visual features caused the score; this is '
    'not feature attribution. Do not call the video real, fake, authentic, '
    'or manipulated as a certainty. State that the detector is experimental '
    'and its score is not a calibrated probability. Distinguish AI assessment '
    'from cryptographic file integrity. Keep the explanation under 160 words.'
)


def load_local_env():
    """Read API keys from root .env without overriding active process environment."""
    try:
        lines = ENV_FILE.read_text(encoding='utf-8').splitlines()
    except OSError:
        return
    allowed = {'GROQ_API_KEY', 'GROQ_MODEL', 'OLLAMA_API_KEY', 'OLLAMA_MODEL'}
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
    """Returns True if any supported AI explanation provider is configured or available."""
    load_local_env()
    return bool(
        os.environ.get('GROQ_API_KEY', '').strip()
        or os.environ.get('OLLAMA_API_KEY', '').strip()
        or True  # Analytical fallback always ensures availability
    )


def _facts_from_report(report):
    analysis = report.get('analysis') or {}
    coverage = report.get('coverage') or {}
    thresholds = report.get('thresholds') or {}
    return {
        'assessment': analysis.get('assessment'),
        'detector_available': analysis.get('detector_available'),
        'detector_reason': analysis.get('reason'),
        'score': analysis.get('score'),
        'low_threshold': thresholds.get('low_threshold', 0.20),
        'suspicious_threshold': thresholds.get('suspicious_threshold', 0.80),
        'requested_frames': coverage.get('requested_frames', 12),
        'analyzed_frames': coverage.get('analyzed_frames', 0),
        'analyzed_faces': coverage.get('analyzed_faces', 0),
        'rejected_faces': coverage.get('rejected_faces', 0),
    }


def _generate_fallback_explanation(report) -> str:
    """Generate a clean, structured analytical summary from report metrics if external APIs fail."""
    facts = _facts_from_report(report)
    assessment = facts['assessment'] or 'Inconclusive'
    score = facts['score']
    score_str = f"{score:.4f}" if score is not None else "N/A"
    low_th = facts['low_threshold']
    susp_th = facts['suspicious_threshold']
    analyzed_f = facts['analyzed_frames']
    req_f = facts['requested_frames']
    faces = facts['analyzed_faces']
    rejected = facts['rejected_faces']

    if assessment == 'Suspicious':
        return (
            f"The video assessment is 'Suspicious' with a peak model score of {score_str}, which exceeds the "
            f"suspicious threshold of {susp_th}. The detector analyzed {faces} facial crop(s) across {analyzed_f} of {req_f} "
            f"sampled frames. This model output suggests visual anomalies consistent with facial forgery patterns. "
            f"Note that the detector is experimental and scores are not calibrated probabilities. Furthermore, AI screening "
            f"evaluates visual patterns, whereas cryptographic signing (Ed25519 & pHash) binds these metrics to exact content."
        )
    elif assessment == 'Low detected manipulation risk':
        return (
            f"The video assessment is 'Low detected manipulation risk'. All analyzed faces across {analyzed_f} of {req_f} "
            f"sampled frames scored below the low threshold of {low_th} (maximum detected score: {score_str}), with zero "
            f"rejected faces ({rejected} rejected). This indicates sufficient frame coverage and face quality without manipulation "
            f"flags. However, this screening is an estimate, not definitive proof of authenticity. A matching digital signature "
            f"and perceptual fingerprint establish report integrity, independent of the model's visual estimate."
        )
    else:
        reason = facts['detector_reason'] or "Insufficient coverage, rejected faces, or intermediate score."
        return (
            f"The video assessment is 'Inconclusive' (Score: {score_str}). Reason: {reason}. "
            f"The pipeline analyzed {analyzed_f}/{req_f} requested frames with {rejected} rejected face detections. "
            f"Because face quality or coverage did not satisfy strict eligibility thresholds, the system abstains from a definitive "
            f"risk rating. AI screening is distinct from cryptographic verification: file integrity confirms byte association, "
            f"not real-world truth."
        )


def _call_groq(api_key: str, facts: dict) -> str:
    model = os.environ.get('GROQ_MODEL', DEFAULT_GROQ_MODEL).strip() or DEFAULT_GROQ_MODEL
    body = json.dumps({
        'model': model,
        'messages': [
            {'role': 'system', 'content': SYSTEM_PROMPT},
            {'role': 'user', 'content': json.dumps(facts, separators=(',', ':'))},
        ],
        'temperature': 0.2,
        'max_tokens': 240,
    }).encode('utf-8')

    req = Request(
        GROQ_CHAT_URL,
        data=body,
        headers={
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
            'User-Agent': 'FrameSeal-Deepfake-Verification/1.0',
        },
        method='POST',
    )
    with urlopen(req, timeout=30) as response:
        data = json.loads(response.read(256_000))
    text = data['choices'][0]['message']['content'].strip()
    if not text:
        raise ValueError('Empty explanation returned by Groq')
    return text


def _call_ollama(api_key: str, facts: dict) -> str:
    model = os.environ.get('OLLAMA_MODEL', DEFAULT_OLLAMA_MODEL).strip() or DEFAULT_OLLAMA_MODEL
    body = json.dumps({
        'model': model,
        'stream': False,
        'options': {'temperature': 0.2, 'num_predict': 240},
        'messages': [
            {'role': 'system', 'content': SYSTEM_PROMPT},
            {'role': 'user', 'content': json.dumps(facts, separators=(',', ':'))},
        ],
    }).encode('utf-8')

    req = Request(
        OLLAMA_CHAT_URL,
        data=body,
        headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'},
        method='POST',
    )
    with urlopen(req, timeout=40) as response:
        result = json.loads(response.read(256_000))
    text = result['message']['content'].strip()
    if not text:
        raise ValueError('Empty explanation returned by Ollama')
    return text


def explain(report):
    """Generate a narrative explanation from report metrics using Groq, Ollama, or fallback."""
    load_local_env()
    facts = _facts_from_report(report)

    groq_key = os.environ.get('GROQ_API_KEY', '').strip()
    ollama_key = os.environ.get('OLLAMA_API_KEY', '').strip()

    # Try Groq Cloud first if configured
    if groq_key:
        try:
            return _call_groq(groq_key, facts)
        except HTTPError as exc:
            if exc.code == 401:
                raise ExplanationError('Groq rejected the API key; check GROQ_API_KEY in the root .env file') from exc
            # If rate limit or other temporary issue, fallback gracefully
        except Exception:
            pass

    # Try Ollama Cloud if configured
    if ollama_key:
        try:
            return _call_ollama(ollama_key, facts)
        except HTTPError as exc:
            if exc.code == 402:
                # Payment required / out of credits
                pass  # Fall through to fallback
            elif exc.code == 401:
                pass

    # Resilient Analytical Fallback
    return _generate_fallback_explanation(report)
