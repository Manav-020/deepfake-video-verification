import { useEffect, useState } from 'react';

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
        <span className="social-badge-icon">{ready ? '🛡️' : '⛔'}</span>
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
      <a className="brand small-brand" href="/">FrameSeal</a>
      <p className="eyebrow">SHARED FILE</p>
      <h1>Video and signed report</h1>
      {error && <p className="notice error">{error}</p>}
      {!error && !report && <p className="muted">Checking this share link…</p>}
      <video className="shared-video" controls src={`/s/${token}/video`} />
      {report && (
        <section className="card">
          <p><strong>Report ID:</strong> {report.report_id}</p>
          <p><strong>AI assessment:</strong> {report.analysis?.assessment || 'Unavailable'}</p>
          <p className="muted">The assessment is an estimate. The signed report binds to exact video bytes and perceptual fingerprints; it does not prove the depicted event is genuine.</p>
          <button className="button secondary" onClick={() => saveJson('signed-report.json', envelope)}>Download signed report</button>
          <a className="button secondary download" href={`/s/${token}/video`} download="analyzed-video.mp4">Download video</a>
        </section>
      )}
    </main>
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
          {isExact && '✓ Tier 1: Exact Byte Match'}
          {isReencoded && '≈ Tier 2: Same Content, Re-encoded'}
          {isAltered && '✗ Tier 3: Content Altered / Mismatch'}
          {isUntrusted && '⚠ Untrusted / Invalid Signature'}
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

function Assessment({
  result,
  onShare,
  onRevoke,
  onDownload,
  onExplain,
  explanation,
  explaining,
  explanationAvailable,
  onRecompressDemo,
  recompressing,
  lastRecompressedBlob
}) {
  const report = result.report;
  const analysis = report.analysis || {};
  const coverage = report.coverage || {};
  const videoInfo = report.video || {};
  const fp = videoInfo.perceptual_fingerprint;

  // Screening readiness
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
          <button className="button primary" onClick={() => onShare(report.report_id)}>
            Create share link
          </button>
        )}
        <button className="button quiet" onClick={() => onRevoke(report.report_id)}>
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
          className="button accent-recompress"
          onClick={() => onRecompressDemo(report.report_id)}
          disabled={recompressing}
        >
          {recompressing ? 'Recompressing video…' : '⚡ Simulate Social Media Compression (Demo)'}
        </button>
      </div>

      {lastRecompressedBlob && (
        <div className="recompress-demo-banner">
          <div>
            <strong>✓ Video recompressed with H.264 (social media transcode simulation)</strong>
            <p>The file bytes and SHA-256 have changed. Verify it below to observe how the Perceptual Fingerprint maintains verification!</p>
          </div>
          <button
            className="button secondary download-btn"
            onClick={() => saveBlob('recompressed-video.mp4', lastRecompressedBlob)}
          >
            Download recompressed MP4
          </button>
        </div>
      )}

      {!explanationAvailable && (
        <p className="muted">
          Add your AI provider API key to the repository root .env file, then restart the backend to enable explanations.
        </p>
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

export default function App() {
  const sharedMatch = window.location.pathname.match(/^\/s\/([A-Za-z0-9_-]{43})\/?$/);
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
      const data = await request('/api/analyze', { method: 'POST', headers: { 'x-csrf-token': csrf }, body });
      setResult(data);
      setFramePreviews(data.previews || []);
      setVerificationData(null);
      setRawVerification('');
      setExplanation('');
      await refreshReports();
      setSelectedVideo('');
      form.reset();
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
      setMessage('Video recompressed (CRF 32)! File downloaded. Upload this video and the signed report to the Verify section below to see the Tier 2 re-encoded match.');
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
        <a className="brand" href="/">FrameSeal</a>
        <span className="tagline">RECOMPRESSION-ROBUST DEEPFAKE SCREENING &amp; SIGNED CONTENT BINDING</span>
        <span className={`status-dot ${status?.model_ready ? 'ready' : ''}`}>
          {status?.model_ready ? 'Model ready' : 'Model unavailable'}
        </span>
      </header>

      <main className="layout">
        <section className="intro">
          <p className="eyebrow">RECOMPRESSION ROBUST · SIGNED ENVELOPES</p>
          <h1>Inspect a video.<br /><em>Verify even after re-encoding.</em></h1>
          <p className="lead">
            FrameSeal screens facial manipulation signals and binds its report to both exact SHA-256 file bytes
            and a robust 64-bit DCT perceptual fingerprint. Even when a video is recompressed by social media,
            its visual authenticity remains verifiable.
          </p>
          <div className="trust-note">
            <strong>3-Tier Content Verification</strong>
            <span>
              1. Exact byte match &middot; 2. Same content re-encoded &middot; 3. Content altered / tampered.
              Social media distribution is guarded against manipulated and altered uploads.
            </span>
          </div>
          {status && (
            <p className="model-status">
              {status.model_status} &middot; Upload limit {status.max_upload_mb} MB &middot; {status.max_duration_seconds}s max
            </p>
          )}
        </section>

        {error && <p className="notice error">{error}</p>}
        {message && <p className="notice success">{message}</p>}

        <section className="card upload-card">
          <div className="section-title">
            <div>
              <p className="eyebrow">01 / SCREEN</p>
              <h2>Analyze a video</h2>
            </div>
            <span className="step">PRIVATE BY DEFAULT</span>
          </div>
          <form onSubmit={analyze}>
            <label className="file-drop">
              <span className="file-icon">↑</span>
              <strong>{selectedVideo || 'Select a video'}</strong>
              <small>
                {selectedVideo ? 'Video selected. Click “Analyze video” below to begin.' : 'Choose an MP4 video, then click Analyze video below.'}
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
            <button className="button primary full" disabled={busy || !csrf}>
              {busy ? 'Analyzing video…' : !csrf ? 'Connecting to backend…' : 'Analyze video'}
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
          />
        )}

        {result && <FrameGallery previews={framePreviews} />}

        <section className="card">
          <div className="section-title">
            <div>
              <p className="eyebrow">02 / VERIFY</p>
              <h2>Check a received file</h2>
            </div>
            <span className="step">RECOMPRESSION-ROBUST</span>
          </div>
          <p className="muted">
            Upload any video and its signed JSON report. FrameSeal evaluates Ed25519 digital signature,
            exact SHA-256 digest, and perceptual frame fingerprints to distinguish exact matches from re-encoded files and altered videos.
          </p>

          <form className="verify-form" onSubmit={verify}>
            <label>
              Video (Original or Re-encoded)
              <input name="video" type="file" accept="video/*,.mp4,.mov,.avi" required />
            </label>
            <label>
              Signed report (.json)
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

        <section className="card">
          <div className="section-title">
            <div>
              <p className="eyebrow">PRIVATE HISTORY</p>
              <h2>Recent reports</h2>
            </div>
            <span className="step">THIS BROWSER SESSION</span>
          </div>
          {reports.length === 0 ? (
            <p className="muted">No reports in this session yet.</p>
          ) : (
            <div className="report-list">
              {reports.map((report) => (
                <div className="report-row" key={report.report_id}>
                  <div>
                    <strong>{report.analysis?.assessment || 'Inconclusive'}</strong>
                    <small>{new Date(report.analyzed_at).toLocaleString()} / {report.report_id}</small>
                    {shareLinks[report.report_id] && (
                      <a className="history-share" href={shareLinks[report.report_id]}>
                        {shareLinks[report.report_id]}
                      </a>
                    )}
                  </div>
                  <div className="row-actions">
                    <button className="text-button" onClick={() => downloadReport(report.report_id)}>
                      Report
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

        <footer>
          FrameSeal &middot; Experimental facial screening &amp; recompression-robust cryptographic content verification.
        </footer>
      </main>
    </div>
  );
}
