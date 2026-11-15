import { useEffect, useState } from 'react';

// --- Professional SVG Icons ---
function IconShieldCheck({ className = "icon" }) {
  return (
    <svg className={className} width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
      <polyline points="9 12 11 14 15 10"/>
    </svg>
  );
}

function IconShieldAlert({ className = "icon" }) {
  return (
    <svg className={className} width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
      <line x1="12" y1="8" x2="12" y2="12"/>
      <line x1="12" y1="16" x2="12.01" y2="16"/>
    </svg>
  );
}

function IconSearch({ className = "icon" }) {
  return (
    <svg className={className} width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="11" cy="11" r="8"/>
      <line x1="21" y1="21" x2="16.65" y2="16.65"/>
    </svg>
  );
}

function IconFileText({ className = "icon" }) {
  return (
    <svg className={className} width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
      <polyline points="14 2 14 8 20 8"/>
      <line x1="16" y1="13" x2="8" y2="13"/>
      <line x1="16" y1="17" x2="8" y2="17"/>
      <line x1="10" y1="9" x2="8" y2="9"/>
    </svg>
  );
}

function IconUpload({ className = "icon" }) {
  return (
    <svg className={className} width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
      <polyline points="17 8 12 3 7 8"/>
      <line x1="12" y1="3" x2="12" y2="15"/>
    </svg>
  );
}

function IconZap({ className = "icon" }) {
  return (
    <svg className={className} width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ marginRight: '6px' }}>
      <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
    </svg>
  );
}

function IconCheck({ className = "icon" }) {
  return (
    <svg className={className} width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="20 6 9 17 4 12"/>
    </svg>
  );
}

function IconRefresh({ className = "icon" }) {
  return (
    <svg className={className} width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="23 4 23 10 17 10"/>
      <polyline points="1 20 1 14 7 14"/>
      <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>
    </svg>
  );
}

function IconAlert({ className = "icon" }) {
  return (
    <svg className={className} width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10"/>
      <line x1="12" y1="8" x2="12" y2="12"/>
      <line x1="12" y1="16" x2="12.01" y2="16"/>
    </svg>
  );
}

// --- API Client ---
async function request(url, options = {}) {
  const response = await fetch(url, { credentials: 'same-origin', ...options });
  const type = response.headers.get('content-type') || '';
  const body = type.includes('application/json') ? await response.json() : await response.text();
  if (!response.ok) throw new Error(body?.detail || `Request failed (${response.status})`);
  return body;
}

function assessmentTone(assessment) {
  if (assessment === 'Suspicious') return 'danger';
  if (assessment === 'Low detected manipulation risk') return 'good';
  return 'neutral';
}

function SocialReadinessBanner({ ready, reason, title }) {
  return (
    <div className={`social-banner ${ready ? 'ready' : 'blocked'}`}>
      <div className="social-banner-header">
        <span className="social-badge-icon">
          {ready ? <IconShieldCheck /> : <IconShieldAlert />}
        </span>
        <div>
          <strong>{title || (ready ? 'READY FOR SOCIAL MEDIA UPLOAD' : 'NOT READY TO UPLOAD (BLOCKED)')}</strong>
          <p>{reason}</p>
        </div>
      </div>
      <small className="social-banner-footnote">
        {ready
          ? 'Content matches authentic low-risk screening. Robust perceptual binding preserves integrity across social media compression.'
          : 'Social Media Guard: Even after video recompression or file re-encoding, manipulated or unverified videos remain blocked.'}
      </small>
    </div>
  );
}

function FrameGallery({ previews }) {
  const validPreviews = Array.isArray(previews) ? previews.filter((frame) => frame?.image) : [];
  if (validPreviews.length === 0) return null;
  return (
    <section className="card frame-gallery">
      <div className="section-title">
        <div>
          <p className="eyebrow">SAMPLED VIDEO FRAMES &amp; PERCEPTUAL FINGERPRINTS</p>
          <h2>Sampled Frame Analysis</h2>
        </div>
      </div>
      <p className="muted">
        Green boxes are scored faces; amber boxes were detected but excluded from scoring.
        Each sampled frame is also fingerprinted via 64-bit DCT perceptual hash for recompression robustness.
      </p>
      <div className="frame-grid">
        {validPreviews.map((frame, index) => {
          const timestamp = Number(frame.timestamp_seconds ?? frame.timestamp ?? 0);
          const frameNumber = Number.isInteger(frame.frame) ? frame.frame : index;
          const faces = Array.isArray(frame.faces) ? frame.faces : [];
          return (
            <article className="frame-item" key={frameNumber}>
              <img
                src={frame.image}
                alt={`Sampled frame ${frameNumber + 1} at ${timestamp.toFixed(2)} seconds with face detections`}
              />
              <div>
                <strong>Frame {frameNumber + 1}</strong>
                <span>{timestamp.toFixed(2)} s · {faces.length ? `${faces.length} face${faces.length === 1 ? '' : 's'}` : 'No faces'}</span>
              </div>
              {faces.length > 0 && (
                <ul>
                  {faces.map((face, faceIndex) => (
                    <li key={faceIndex}>
                      {face.model_score != null
                        ? `Face ${faceIndex + 1}: score ${Number(face.model_score).toFixed(4)}`
                        : `Face ${faceIndex + 1}: excluded — ${face.rejected || 'not scored'}`}
                    </li>
                  ))}
                </ul>
              )}
            </article>
          );
        })}
      </div>
    </section>
  );
}

function saveJson(name, value) {
  const url = URL.createObjectURL(new Blob([JSON.stringify(value, null, 2)], { type: 'application/json' }));
  const link = document.createElement('a');
  link.href = url;
  link.download = name;
  link.click();
  URL.revokeObjectURL(url);
}

function saveBlob(name, blob) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = name;
  link.click();
  URL.revokeObjectURL(url);
}

function SharedVideo({ token }) {
  const [report, setReport] = useState(null);
  const [envelope, setEnvelope] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    request(`/s/${token}/report`).then((signed) => {
      const raw = Uint8Array.from(atob(signed.payload), (character) => character.charCodeAt(0));
      setEnvelope(signed);
      setReport(JSON.parse(new TextDecoder().decode(raw)));
    }).catch((e) => setError(e.message));
  }, [token]);

  return (
    <main className="share-page">
      <a className="brand small-brand" href="/">DeepFake Detection System</a>
      <p className="eyebrow">SHARED FILE</p>
      <h1>Video and signed report</h1>
      {error && <p className="notice error">{error}</p>}
      {!error && !report && <p className="muted">Checking this share link…</p>}
      <video className="shared-video" controls playsInline preload="metadata" src={`/s/${token}/video`} />
      {report && (
        <section className="card">
          <p><strong>Report ID:</strong> {report.report_id}</p>
          <p><strong>AI assessment:</strong> {report.analysis?.assessment || 'Unavailable'}</p>
          <p className="muted">The assessment is an estimate. The signed report binds to exact video bytes and perceptual fingerprints; it does not prove the depicted event is genuine.</p>
          <button className="button secondary" onClick={() => saveJson('signed-report.json', envelope)}>Download signed report</button>
          <a className="button secondary download" href={`/s/${token}/video?download=1`} download="analyzed-video.mp4">Download video</a>
        </section>
      )}
    </main>
  );
}

function HomePage({ onNavigate, status }) {
  return (
    <div className="page-home">
      <section className="intro">
        <p className="eyebrow">CRYPTOGRAPHIC SCREENING &amp; PERCEPTUAL BINDING</p>
        <h1>DeepFake Detection System</h1>
        <p className="lead">
          Screen facial videos for deepfake anomalies, generate Ed25519-signed canonical reports,
          and verify visual content authenticity across social media compression and re-encoding.
        </p>
        <div className="trust-note">
          <strong>3-Tier Verification Engine</strong>
          <span>
            Separates exact SHA-256 byte matching from 64-bit DCT perceptual fingerprinting.
            Manipulated videos remain strictly blocked from social media distribution even after transcoding.
          </span>
        </div>
      </section>

      <div className="home-action-grid">
        <div className="home-card" onClick={() => onNavigate('screen')}>
          <div className="home-card-icon"><IconSearch /></div>
          <h3>Screen a Video</h3>
          <p>Upload any MP4 video to sample frames, run EfficientNet-B7 CPU inference, and generate a tamper-evident signed report.</p>
          <button className="button primary">Go to Screening →</button>
        </div>

        <div className="home-card" onClick={() => onNavigate('verify')}>
          <div className="home-card-icon"><IconShieldCheck /></div>
          <h3>Verify Received File</h3>
          <p>Check any video against its signed report. Determine if it is an exact byte match, re-encoded, or content-altered.</p>
          <button className="button secondary">Go to Verification →</button>
        </div>

        <div className="home-card" onClick={() => onNavigate('history')}>
          <div className="home-card-icon"><IconFileText /></div>
          <h3>Recent Reports</h3>
          <p>Audit and inspect prior screening envelopes, download signed JSON files, or manage active share links.</p>
          <button className="button secondary">View Reports →</button>
        </div>
      </div>

      <section className="card benchmark-card">
        <div className="section-title">
          <div>
            <p className="eyebrow">BENCHMARK EVALUATION</p>
            <h2>Empirical Performance on Celeb-DF v2</h2>
          </div>
          <span className="pill good">Evaluated Benchmark</span>
        </div>
        <p className="muted">
          Tested on a balanced, leak-free test split of the Celeb-DF v2 benchmark (40 videos: 20 real YouTube-real, 20 fake Celeb-synthesis across independent identities):
        </p>

        <div className="stats benchmark-stats">
          <div>
            <span>ROC-AUC</span>
            <strong className="stat-highlight">93.3%</strong>
          </div>
          <div>
            <span>Fake Recall</span>
            <strong className="stat-highlight">100.0%</strong>
            <small>0 / 20 false negatives</small>
          </div>
          <div>
            <span>F1 Score</span>
            <strong className="stat-highlight">87.0%</strong>
          </div>
          <div>
            <span>Accuracy</span>
            <strong className="stat-highlight">80.6%</strong>
            <small>25 / 31 decided</small>
          </div>
        </div>

        <div className="benchmark-footnote">
          <span>Tested with 64-bit DCT pHash perceptual binding &middot; Ed25519 digital signatures &middot; Groq LLaMA 3.3 narrative explanations</span>
        </div>
      </section>
    </div>
  );
}

function Assessment({
  result,
  activeVideoUrl,
  onShare,
  onRevoke,
  onDownload,
  onExplain,
  explanation,
  explaining,
  explanationAvailable,
  onRecompressDemo,
  recompressing,
  lastRecompressedBlob,
  onNavigateToVerify
}) {
  const report = result.report;
  const analysis = report.analysis || {};
  const coverage = report.coverage || {};
  const videoInfo = report.video || {};
  const fp = videoInfo.perceptual_fingerprint;
  const videoSrc = activeVideoUrl || (report.report_id ? `/api/reports/${report.report_id}/video` : '');

  const isLowRisk = analysis.assessment === 'Low detected manipulation risk';
  const isSuspicious = analysis.assessment === 'Suspicious';
  const readinessTitle = isLowRisk
    ? 'APPROVED FOR SOCIAL MEDIA UPLOAD'
    : 'NOT READY TO UPLOAD (BLOCKED)';
  const readinessReason = isLowRisk
    ? 'Screening detected low manipulation risk. Ready to sign and distribute.'
    : isSuspicious
      ? 'NOT READY TO UPLOAD: Facial manipulation / deepfake artifacts detected. Distribution blocked.'
      : 'NOT READY TO UPLOAD: Analysis is inconclusive. Do not distribute without manual review.';

  return (
    <section className="card result-card">
      <div className="card-heading">
        <div>
          <p className="eyebrow">AI ASSESSMENT</p>
          <h2>{analysis.assessment || 'Inconclusive'}</h2>
        </div>
        <span className={`pill ${assessmentTone(analysis.assessment)}`}>
          {analysis.detector_available ? 'Detector available' : 'Detector unavailable'}
        </span>
      </div>

      <p className="muted">{analysis.reason || 'No additional reason provided.'}</p>

      {/* Video Preview Player */}
      {videoSrc && (
        <div className="screening-video-box">
          <video
            className="screening-video"
            controls
            playsInline
            preload="metadata"
            key={videoSrc}
            src={videoSrc}
          />
          <div className="video-player-footer">
            <span>Video Playback</span>
            <code>ID: {report.report_id}</code>
          </div>
        </div>
      )}

      {/* Social Media Readiness Guardrail */}
      <SocialReadinessBanner
        ready={isLowRisk}
        title={readinessTitle}
        reason={readinessReason}
      />

      <div className="stats">
        <div>
          <span>Model score</span>
          <strong>{analysis.score == null ? '—' : Number(analysis.score).toFixed(4)}</strong>
        </div>
        <div>
          <span>Analyzed frames</span>
          <strong>{coverage.analyzed_frames ?? 0} / {coverage.requested_frames ?? 0}</strong>
        </div>
        <div>
          <span>Analyzed faces</span>
          <strong>{coverage.analyzed_faces ?? 0}</strong>
        </div>
      </div>

      <div className="binding-meta">
        <p className="digest">
          <span>SHA-256 (Original video bytes)</span>
          <code>{videoInfo.sha256}</code>
        </p>
        {fp && (
          <p className="digest">
            <span>Perceptual Fingerprint ({fp.algorithm || 'DCT pHash'})</span>
            <code>{fp.sample_frames} sampled frame hashes signed into report</code>
          </p>
        )}
      </div>

      <div className="actions">
        <button className="button secondary" onClick={() => onDownload(report.report_id)}>
          Download signed report
        </button>
        {report.sharing_policy?.allowed && (
          <button className="button secondary" onClick={() => onShare(report.report_id)}>
            Create share link
          </button>
        )}
        <button className="button secondary" onClick={() => onRevoke(report.report_id)}>
          Revoke shares
        </button>
        <button
          className="button secondary"
          onClick={() => onExplain(report.report_id)}
          disabled={!explanationAvailable || explaining}
        >
          {explaining ? 'Writing explanation…' : 'Explain this result'}
        </button>
        <button
          className="button secondary"
          onClick={() => onRecompressDemo(report.report_id)}
          disabled={recompressing}
        >
          {recompressing ? 'Recompressing video…' : 'Social Media Compression'}
        </button>
      </div>

      {lastRecompressedBlob && (
        <div className="recompress-demo-banner">
          <div>
            <strong>Video recompressed with H.264 (transcode simulation)</strong>
            <p>The file bytes and SHA-256 have changed. Verify it to observe how the Perceptual Fingerprint maintains verification!</p>
          </div>
          <div className="recompress-banner-actions">
            <button
              className="button secondary download-btn"
              onClick={() => saveBlob('recompressed-video.mp4', lastRecompressedBlob)}
            >
              Download recompressed MP4
            </button>
            <button
              className="button primary"
              onClick={onNavigateToVerify}
            >
              Verify This Recompressed Video →
            </button>
          </div>
        </div>
      )}

      {explanation && (
        <div className="explanation">
          <strong>AI-generated explanation</strong>
          <p>{explanation}</p>
          <small>Narrative summary of the reported metrics; not a model feature attribution or a separate authenticity check.</small>
        </div>
      )}

      {result.shareUrl && (
        <p className="notice success">
          Share link: <a href={result.shareUrl}>{result.shareUrl}</a>
        </p>
      )}

      <p className="footnote">
        A signed report, matching SHA-256, and perceptual fingerprint establish report integrity and recompression-robust content binding.
        They do not prove the video depicts an authentic real-world event.
      </p>
    </section>
  );
}

function VerificationOutcomeView({ data }) {
  if (!data) return null;
  const outcome = data.verification_outcome;
  const isExact = outcome === 'exact_match';
  const isReencoded = outcome === 'reencoded_match';
  const isAltered = outcome === 'content_altered';
  const isUntrusted = outcome === 'untrusted_or_invalid';

  const similarityPct = data.fingerprint_similarity != null
    ? (data.fingerprint_similarity * 100).toFixed(1)
    : '0.0';

  return (
    <div className="verify-result-container">
      <div className="verify-tier-header">
        <div>
          <p className="eyebrow">3-TIER VERIFICATION OUTCOME</p>
          <h3>{data.outcome_label || 'Verification Outcome'}</h3>
        </div>
        <span className={`tier-badge ${outcome}`}>
          {isExact && <><IconCheck /> Tier 1: Exact Byte Match</>}
          {isReencoded && <><IconRefresh /> Tier 2: Same Content, Re-encoded</>}
          {isAltered && <><IconAlert /> Tier 3: Content Altered / Mismatch</>}
          {isUntrusted && <><IconAlert /> Untrusted / Invalid Signature</>}
        </span>
      </div>

      <p className="verify-detail-text">{data.outcome_detail}</p>

      {/* Social Media Readiness Banner */}
      <SocialReadinessBanner
        ready={data.social_media_ready}
        reason={data.social_media_reason}
      />

      {/* Perceptual Similarity Meter */}
      <div className="similarity-meter-box">
        <div className="similarity-labels">
          <span>Visual Perceptual Similarity</span>
          <strong>{similarityPct}%</strong>
        </div>
        <div className="meter-track">
          <div
            className={`meter-fill ${data.content_matches ? 'good' : 'danger'}`}
            style={{ width: `${Math.min(100, Math.max(0, parseFloat(similarityPct)))}%` }}
          />
        </div>
        <div className="similarity-subtext">
          <span>Threshold: 82.0% for content identity</span>
          <span>{data.content_matches ? 'Visual structure matches original' : 'Significant deviation detected'}</span>
        </div>
      </div>

      {/* 4-Check Matrix */}
      <div className="checks-grid">
        <div className={`check-card ${data.signature_valid ? 'pass' : 'fail'}`}>
          <div className="check-type">Ed25519 Signature</div>
          <strong>{data.signature_valid ? 'Valid Signature' : 'Invalid / Untrusted'}</strong>
          <small>{data.signature_status}</small>
        </div>

        <div className={`check-card ${data.hash_matches ? 'pass' : 'neutral'}`}>
          <div className="check-type">SHA-256 Byte Hash</div>
          <strong>{data.hash_matches ? 'Exact Byte Match' : 'Byte Hash Mismatch'}</strong>
          <small>{data.hash_matches ? 'Exact original file bytes' : 'Byte modified or re-encoded'}</small>
        </div>

        <div className={`check-card ${data.content_matches ? 'pass' : 'fail'}`}>
          <div className="check-type">Perceptual Fingerprint</div>
          <strong>{data.content_matches ? 'Content Matches' : 'Content Altered'}</strong>
          <small>{similarityPct}% similarity across frames</small>
        </div>

        <div className="check-card neutral">
          <div className="check-type">Report Assessment</div>
          <strong>{data.signed_ai_assessment || data.claimed_ai_assessment || 'Inconclusive'}</strong>
          <small>ID: {data.report_id?.slice(0, 12)}…</small>
        </div>
      </div>
    </div>
  );
}

export default function App() {
  const sharedMatch = window.location.pathname.match(/^\/s\/([A-Za-z0-9_-]{43})\/?$/);
  const [currentPage, setCurrentPage] = useState('home');
  const [csrf, setCsrf] = useState('');
  const [status, setStatus] = useState(null);
  const [reports, setReports] = useState([]);
  const [result, setResult] = useState(null);
  const [framePreviews, setFramePreviews] = useState([]);
  const [shareLinks, setShareLinks] = useState({});
  const [selectedVideo, setSelectedVideo] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [verificationData, setVerificationData] = useState(null);
  const [rawVerification, setRawVerification] = useState('');
  const [showRawJson, setShowRawJson] = useState(false);
  const [explanation, setExplanation] = useState('');
  const [explaining, setExplaining] = useState(false);
  const [recompressing, setRecompressing] = useState(false);
  const [lastRecompressedBlob, setLastRecompressedBlob] = useState(null);

  useEffect(() => {
    if (sharedMatch) return;
    request('/api/session').then((session) => {
      setCsrf(session.csrf_token);
      return Promise.all([request('/api/status'), request('/api/reports')]);
    }).then(([nextStatus, nextReports]) => {
      setStatus(nextStatus);
      setReports(nextReports);
    }).catch((e) => setError(e.message));
  }, []);

  if (sharedMatch) return <SharedVideo token={sharedMatch[1]} />;

  async function refreshReports() {
    setReports(await request('/api/reports'));
  }

  async function analyze(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const video = form.elements.video.files[0];
    if (!video) return;
    setBusy(true); setError(''); setMessage(''); setLastRecompressedBlob(null);
    try {
      const body = new FormData();
      body.append('video', video);
      const framesVal = parseInt(form.elements.max_frames?.value, 10);
      body.append('max_frames', isNaN(framesVal) ? 12 : Math.max(1, Math.min(64, framesVal)));
      const data = await request('/api/analyze', { method: 'POST', headers: { 'x-csrf-token': csrf }, body });
      setResult(data);
      setFramePreviews(data.previews || []);
      setExplanation('');
      await refreshReports();
      setSelectedVideo('');
      form.reset();
      setMessage('Analysis complete. Detailed assessment and frame analysis are shown below.');
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  async function verify(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const video = form.elements.video.files[0];
    const report = form.elements.report.files[0];
    if (!video || !report) return;
    setBusy(true); setError(''); setMessage('');
    try {
      const body = new FormData();
      body.append('video', video);
      body.append('report', report);
      const data = await request('/api/verify', { method: 'POST', headers: { 'x-csrf-token': csrf }, body });
      setVerificationData(data);
      setRawVerification(JSON.stringify(data, null, 2));
      setMessage('Verification complete. Review 3-tier outcome, perceptual similarity, and social media readiness.');
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  async function recompressDemo(reportId) {
    setError(''); setMessage(''); setRecompressing(true);
    try {
      const body = new FormData();
      body.append('report_id', reportId);
      body.append('crf', '32');
      const response = await fetch('/api/demo/recompress', {
        method: 'POST',
        headers: { 'x-csrf-token': csrf },
        credentials: 'same-origin',
        body
      });
      if (!response.ok) {
        const text = await response.text();
        throw new Error(text || 'Recompression failed');
      }
      const blob = await response.blob();
      setLastRecompressedBlob(blob);
      saveBlob('recompressed-video.mp4', blob);
      setMessage('Video recompressed (CRF 32)! File downloaded. You can now verify it on the Check Received File page to observe Tier 2 re-encoded verification.');
    } catch (e) {
      setError(e.message);
    } finally {
      setRecompressing(false);
    }
  }

  async function share(id) {
    setError(''); setMessage('');
    try {
      const data = await request(`/api/reports/${id}/share`, { method: 'POST', headers: { 'x-csrf-token': csrf } });
      const url = new URL(data.url, window.location.origin).href;
      setShareLinks((current) => ({ ...current, [id]: url }));
      setResult((current) => current?.report.report_id === id ? { ...current, shareUrl: url } : current);
    } catch (e) {
      setError(e.message);
    }
  }

  async function revoke(id) {
    setError(''); setMessage('');
    try {
      await request(`/api/reports/${id}/revoke`, { method: 'POST', headers: { 'x-csrf-token': csrf } });
      setMessage(`All share links for report ${id} have been revoked.`);
    } catch (e) {
      setError(e.message);
    }
  }

  async function downloadReport(id) {
    try {
      const data = await request(`/api/reports/${id}`);
      saveJson(`${id}-signed-report.json`, data.envelope);
    } catch (e) {
      setError(e.message);
    }
  }

  async function viewReportDetails(id) {
    try {
      setBusy(true);
      const data = await request(`/api/reports/${id}`);
      setResult(data);
      setFramePreviews(data.previews || []);
      setCurrentPage('screen');
      setMessage(`Viewing saved report ${id}`);
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  async function explain(id) {
    setError(''); setExplanation(''); setExplaining(true);
    try {
      const data = await request(`/api/reports/${id}/explanation`, { method: 'POST', headers: { 'x-csrf-token': csrf } });
      setExplanation(data.explanation);
    } catch (e) {
      setError(e.message);
    } finally {
      setExplaining(false);
    }
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <a className="brand" href="#" onClick={(e) => { e.preventDefault(); setCurrentPage('home'); }}>
          DeepFake Detection System
        </a>

        <nav className="nav-tabs">
          <button
            className={`nav-tab ${currentPage === 'home' ? 'active' : ''}`}
            onClick={() => setCurrentPage('home')}
          >
            Home
          </button>
          <button
            className={`nav-tab ${currentPage === 'screen' ? 'active' : ''}`}
            onClick={() => setCurrentPage('screen')}
          >
            Video Upload &amp; Screening
          </button>
          <button
            className={`nav-tab ${currentPage === 'verify' ? 'active' : ''}`}
            onClick={() => setCurrentPage('verify')}
          >
            Check Received File
          </button>
          <button
            className={`nav-tab ${currentPage === 'history' ? 'active' : ''}`}
            onClick={() => setCurrentPage('history')}
          >
            Recent Reports {reports.length > 0 && <span className="tab-count">{reports.length}</span>}
          </button>
        </nav>

        <span className={`status-dot ${status?.model_ready ? 'ready' : ''}`}>
          {status?.model_ready ? 'Model ready' : 'Model unavailable'}
        </span>
      </header>

      <main className="layout">
        {error && (
          <div className="notice error notice-dismissible">
            <span>{error}</span>
            <button className="notice-close" onClick={() => setError("")} aria-label="Dismiss">&times;</button>
          </div>
        )}
        {message && (
          <div className="notice success notice-dismissible">
            <span>{message}</span>
            <button className="notice-close" onClick={() => setMessage("")} aria-label="Dismiss">&times;</button>
          </div>
        )}

        {/* PAGE 1: HOME */}
        {currentPage === 'home' && (
          <HomePage onNavigate={setCurrentPage} status={status} />
        )}

        {/* PAGE 2: VIDEO UPLOAD & SCREENING */}
        {currentPage === 'screen' && (
          <div className="page-screen">
            <section className="card upload-card">
              <div className="section-title">
                <div>
                  <p className="eyebrow">01 / SCREENING</p>
                  <h2>Upload a video to analyze</h2>
                </div>
                <span className="step">LOCAL FIRST</span>
              </div>
              <p className="muted">
                Upload any MP4 video to sample frames, detect facial manipulation, inspect bounding crops,
                and generate an Ed25519-signed report with 64-bit DCT perceptual hashes.
              </p>
              <form onSubmit={analyze}>
                <label className="file-drop">
                  <span className="file-icon"><IconUpload /></span>
                  <strong>{selectedVideo || 'Select a video to analyze'}</strong>
                  <small>
                    {selectedVideo ? 'File ready. Click “Analyze video” below to begin.' : 'Click to choose an MP4, MOV, or AVI video'}
                  </small>
                  <input
                    name="video"
                    type="file"
                    accept="video/*,.mp4,.mov,.avi"
                    required
                    onChange={(event) => {
                      setSelectedVideo(event.target.files[0]?.name || '');
                      setError('');
                    }}
                  />
                </label>
                <div className="frames-row">
                  <label className="frames-label" htmlFor="max_frames">Frames to sample</label>
                  <input
                    id="max_frames"
                    name="max_frames"
                    type="number"
                    className="frames-input"
                    min={1}
                    max={64}
                    defaultValue={12}
                  />
                  <span className="frames-hint">1 – 64</span>
                </div>
                <button className="button primary full" disabled={busy || !csrf}>
                  {busy ? 'Analyzing video (sampling & inference)…' : !csrf ? 'Connecting to backend…' : 'Analyze video'}
                </button>
              </form>
            </section>

            {result && (
              <Assessment
                result={result}
                onShare={share}
                onRevoke={revoke}
                onDownload={downloadReport}
                onExplain={explain}
                explanation={explanation}
                explaining={explaining}
                explanationAvailable={status?.explanation_available}
                onRecompressDemo={recompressDemo}
                recompressing={recompressing}
                lastRecompressedBlob={lastRecompressedBlob}
                onNavigateToVerify={() => setCurrentPage('verify')}
              />
            )}

            {result && <FrameGallery previews={framePreviews} />}
          </div>
        )}

        {/* PAGE 3: CHECK RECEIVED FILE (VERIFY) */}
        {currentPage === 'verify' && (
          <div className="page-verify">
            <section className="card">
              <div className="section-title">
                <div>
                  <p className="eyebrow">02 / VERIFY</p>
                  <h2>Check a received video &amp; report</h2>
                </div>
                <span className="step">3-TIER BINDING</span>
              </div>
              <p className="muted">
                Upload the video and its signed JSON report. The system evaluates the Ed25519 digital signature,
                exact SHA-256 byte digest, and 64-bit DCT perceptual fingerprint to detect if the video is an exact match,
                re-encoded (e.g. social media compressed), or altered.
              </p>

              <form className="verify-form" onSubmit={verify}>
                <label>
                  Video (Original or Re-encoded MP4)
                  <input name="video" type="file" accept="video/*,.mp4,.mov,.avi" required />
                </label>
                <label>
                  Signed report (.json envelope)
                  <input name="report" type="file" accept="application/json,.json" required />
                </label>
                <button className="button secondary" disabled={busy || !csrf}>
                  {busy ? 'Verifying…' : 'Verify report'}
                </button>
              </form>

              {verificationData && <VerificationOutcomeView data={verificationData} />}

              {rawVerification && (
                <div className="raw-json-toggle">
                  <button
                    type="button"
                    className="text-button"
                    onClick={() => setShowRawJson(!showRawJson)}
                  >
                    {showRawJson ? 'Hide raw JSON data' : 'View raw JSON payload'}
                  </button>
                  {showRawJson && <pre className="verification">{rawVerification}</pre>}
                </div>
              )}
            </section>
          </div>
        )}

        {/* PAGE 4: RECENT REPORTS */}
        {currentPage === 'history' && (
          <div className="page-history">
            <section className="card">
              <div className="section-title">
                <div>
                  <p className="eyebrow">AUDIT TRAIL</p>
                  <h2>Recent signed reports</h2>
                </div>
                <span className="step">THIS BROWSER SESSION</span>
              </div>
              <p className="muted">
                Signed reports created in this private session. Each report contains the canonical assessment,
                file SHA-256 digest, and perceptual frame fingerprints.
              </p>

              {reports.length === 0 ? (
                <p className="muted">No reports generated in this session yet.</p>
              ) : (
                <div className="report-list">
                  {reports.map((report) => (
                    <div className="report-row" key={report.report_id}>
                      <div>
                        <strong>{report.analysis?.assessment || 'Inconclusive'}</strong>
                        <small>{new Date(report.analyzed_at).toLocaleString()} &middot; ID: {report.report_id}</small>
                        {shareLinks[report.report_id] && (
                          <a className="history-share" href={shareLinks[report.report_id]}>
                            Share: {shareLinks[report.report_id]}
                          </a>
                        )}
                      </div>
                      <div className="row-actions">
                        <button className="button secondary sm-btn" onClick={() => viewReportDetails(report.report_id)}>
                          View Details
                        </button>
                        <button className="text-button" onClick={() => downloadReport(report.report_id)}>
                          Download
                        </button>
                        {report.sharing_policy?.allowed && (
                          <button className="text-button" onClick={() => share(report.report_id)}>
                            Share
                          </button>
                        )}
                        <button className="text-button" onClick={() => revoke(report.report_id)}>
                          Revoke
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </section>
          </div>
        )}

        <footer>
          DeepFake Detection System &middot; Recompression-robust cryptographic content verification &amp; facial forgery screening.
        </footer>
      </main>
    </div>
  );
}
