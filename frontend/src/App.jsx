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

function saveJson(name, value) {
  const url = URL.createObjectURL(new Blob([JSON.stringify(value, null, 2)], { type: 'application/json' }));
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
          <p className="muted">The assessment is an estimate. The signed report binds to exact video bytes; it does not prove the depicted event is genuine.</p>
          <button className="button secondary" onClick={() => saveJson('signed-report.json', envelope)}>Download signed report</button>
          <a className="button secondary download" href={`/s/${token}/video`} download="analyzed-video.mp4">Download video</a>
        </section>
      )}
    </main>
  );
}

function Assessment({ result, onShare, onRevoke, onDownload }) {
  const report = result.report;
  const analysis = report.analysis || {};
  const coverage = report.coverage || {};
  return (
    <section className="card result-card">
      <div className="card-heading"><div><p className="eyebrow">AI ASSESSMENT</p><h2>{analysis.assessment || 'Inconclusive'}</h2></div>
        <span className={`pill ${assessmentTone(analysis.assessment)}`}>{analysis.detector_available ? 'Detector available' : 'Detector unavailable'}</span>
      </div>
      <p className="muted">{analysis.reason || 'No additional reason provided.'}</p>
      <div className="stats">
        <div><span>Model score</span><strong>{analysis.score == null ? '—' : Number(analysis.score).toFixed(4)}</strong></div>
        <div><span>Analyzed frames</span><strong>{coverage.analyzed_frames ?? 0} / {coverage.requested_frames ?? 0}</strong></div>
        <div><span>Analyzed faces</span><strong>{coverage.analyzed_faces ?? 0}</strong></div>
      </div>
      <p className="digest"><span>SHA-256 of original video</span><code>{report.video?.sha256}</code></p>
      <div className="actions">
        <button className="button secondary" onClick={() => onDownload(report.report_id)}>Download signed report</button>
        {report.sharing_policy?.allowed && <button className="button primary" onClick={() => onShare(report.report_id)}>Create share link</button>}
        <button className="button quiet" onClick={() => onRevoke(report.report_id)}>Revoke shares</button>
      </div>
      {result.shareUrl && <p className="notice success">Share link: <a href={result.shareUrl}>{result.shareUrl}</a></p>}
      <p className="footnote">A signed report and matching hash establish report integrity and file association. They do not prove the video depicts a genuine event.</p>
    </section>
  );
}

export default function App() {
  const sharedMatch = window.location.pathname.match(/^\/s\/([A-Za-z0-9_-]{43})\/?$/);
  const [csrf, setCsrf] = useState('');
  const [status, setStatus] = useState(null);
  const [reports, setReports] = useState([]);
  const [result, setResult] = useState(null);
  const [shareLinks, setShareLinks] = useState({});
  const [selectedVideo, setSelectedVideo] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [verification, setVerification] = useState('');

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
    setBusy(true); setError(''); setMessage('');
    try {
      const body = new FormData(); body.append('video', video);
      const data = await request('/api/analyze', { method: 'POST', headers: { 'x-csrf-token': csrf }, body });
      setResult(data); setVerification(''); await refreshReports();
      setSelectedVideo('');
      form.reset();
    } catch (e) { setError(e.message); }
    finally { setBusy(false); }
  }

  async function verify(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const video = form.elements.video.files[0];
    const report = form.elements.report.files[0];
    if (!video || !report) return;
    setBusy(true); setError(''); setMessage('');
    try {
      const body = new FormData(); body.append('video', video); body.append('report', report);
      setVerification(JSON.stringify(await request('/api/verify', { method: 'POST', headers: { 'x-csrf-token': csrf }, body }), null, 2));
      setMessage('Verification complete. Review the signature and hash results separately.');
    } catch (e) { setError(e.message); }
    finally { setBusy(false); }
  }

  async function share(id) {
    setError(''); setMessage('');
    try {
      const data = await request(`/api/reports/${id}/share`, { method: 'POST', headers: { 'x-csrf-token': csrf } });
      const url = new URL(data.url, window.location.origin).href;
      setShareLinks((current) => ({ ...current, [id]: url }));
      setResult((current) => current?.report.report_id === id ? { ...current, shareUrl: url } : current);
    } catch (e) { setError(e.message); }
  }

  async function revoke(id) {
    setError(''); setMessage('');
    try {
      await request(`/api/reports/${id}/revoke`, { method: 'POST', headers: { 'x-csrf-token': csrf } });
      setMessage(`All share links for report ${id} have been revoked.`);
    } catch (e) { setError(e.message); }
  }

  async function downloadReport(id) {
    try {
      const data = await request(`/api/reports/${id}`);
      saveJson(`${id}-signed-report.json`, data.envelope);
    } catch (e) { setError(e.message); }
  }

  return (
    <div className="app-shell">
      <header className="topbar"><a className="brand" href="/">FrameSeal</a><span className="tagline">PRIVATE VIDEO SCREENING &amp; FILE VERIFICATION</span><span className={`status-dot ${status?.model_ready ? 'ready' : ''}`}>{status?.model_ready ? 'Model ready' : 'Model unavailable'}</span></header>
      <main className="layout">
        <section className="intro"><p className="eyebrow">LOCAL FIRST · SIGNED REPORTS</p><h1>Inspect a video.<br /><em>Verify its exact bytes.</em></h1><p className="lead">FrameSeal screens sampled faces for manipulation signals, then binds its report to the original file with a digital signature.</p><div className="trust-note"><strong>Two separate checks</strong><span>AI screening is an estimate. A valid signature and matching hash verify the report and file association, not the truth of the video.</span></div>
          {status && <p className="model-status">{status.model_status} · Upload limit {status.max_upload_mb} MB · {status.max_duration_seconds}s max</p>}
        </section>

        {error && <p className="notice error">{error}</p>}
        {message && <p className="notice success">{message}</p>}

        <section className="card upload-card"><div className="section-title"><div><p className="eyebrow">01 / SCREEN</p><h2>Analyze a video</h2></div><span className="step">PRIVATE BY DEFAULT</span></div>
          <form onSubmit={analyze}><label className="file-drop"><span className="file-icon">↑</span><strong>{selectedVideo || 'Select a video'}</strong><small>{selectedVideo ? 'Video selected. Click “Analyze video” below to begin.' : 'Choose a file, then click Analyze video below.'}</small><input name="video" type="file" accept="video/*,.mp4,.mov,.avi" required onChange={(event) => { setSelectedVideo(event.target.files[0]?.name || ''); setError(''); }} /></label><button className="button primary full" disabled={busy || !csrf}>{busy ? 'Analyzing video…' : !csrf ? 'Connecting to backend…' : 'Analyze video'}</button></form>
        </section>

        {result && <Assessment result={result} onShare={share} onRevoke={revoke} onDownload={downloadReport} />}

        <section className="card"><div className="section-title"><div><p className="eyebrow">02 / VERIFY</p><h2>Check a received file</h2></div></div><p className="muted">Upload the video and its signed JSON report. Signature validity and exact-file hash matching are reported independently.</p>
          <form className="verify-form" onSubmit={verify}><label>Video<input name="video" type="file" accept="video/*,.mp4,.mov,.avi" required /></label><label>Signed report<input name="report" type="file" accept="application/json,.json" required /></label><button className="button secondary" disabled={busy || !csrf}>Verify report</button></form>
          {verification && <pre className="verification">{verification}</pre>}
        </section>

        <section className="card"><div className="section-title"><div><p className="eyebrow">PRIVATE HISTORY</p><h2>Recent reports</h2></div><span className="step">THIS BROWSER SESSION</span></div>
          {reports.length === 0 ? <p className="muted">No reports in this session yet.</p> : <div className="report-list">{reports.map((report) => <div className="report-row" key={report.report_id}><div><strong>{report.analysis?.assessment || 'Inconclusive'}</strong><small>{new Date(report.analyzed_at).toLocaleString()} / {report.report_id}</small>{shareLinks[report.report_id] && <a className="history-share" href={shareLinks[report.report_id]}>{shareLinks[report.report_id]}</a>}</div><div className="row-actions"><button className="text-button" onClick={() => downloadReport(report.report_id)}>Report</button>{report.sharing_policy?.allowed && <button className="text-button" onClick={() => share(report.report_id)}>Share</button>}<button className="text-button" onClick={() => revoke(report.report_id)}>Revoke</button></div></div>)}</div>}
        </section>
        <footer>Experimental facial screening. Scores are not calibrated probabilities; no labeled dataset performance has been measured.</footer>
      </main>
    </div>
  );
}
