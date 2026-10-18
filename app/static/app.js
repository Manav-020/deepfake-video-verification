'use strict';
let csrf = '', current = null;
const $ = id => document.getElementById(id);
const el = (tag, text, cls) => { const node = document.createElement(tag); node.textContent = text; if (cls) node.className = cls; return node; };
async function api(url, options = {}) {
  options.headers = {...options.headers, 'X-CSRF-Token': csrf};
  const response = await fetch(url, options);
  const text = await response.text();
  let data; try { data = JSON.parse(text); } catch { data = {detail: text || 'Request failed'}; }
  if (!response.ok) throw Error(typeof data.detail === 'string' ? data.detail : 'Invalid request');
  return data;
}
function display(data) {
  current = data;
  const r = data.report, box = $('results'); box.replaceChildren(); box.className = '';
  box.append(el('div', r.analysis.assessment, 'assessment' + (r.analysis.assessment === 'Low detected manipulation risk' ? '' : ' warning')));
  box.append(el('p', r.analysis.reason));
  box.append(el('div', 'Maximum face model score: ' + (r.analysis.score == null ? 'Unavailable' : r.analysis.score.toFixed(4)) + ' · provisional thresholds', 'detail'));
  box.append(el('div', `${r.coverage.analyzed_frames || 0} analyzed frames · ${r.coverage.analyzed_faces || 0} analyzed faces · ${r.coverage.rejected_faces || 0} rejected faces`, 'detail'));
  box.append(el('div', 'Report signed by service · exact file SHA-256:', 'detail'), el('code', r.video.sha256));
  const details = el('details', ''); details.append(el('summary', 'View signed analysis and coverage'), el('pre', JSON.stringify(r, null, 2))); box.append(details);
  $('sharing').hidden = false; $('share-button').disabled = !r.sharing_policy.allowed;
  $('share-policy').textContent = r.sharing_policy.allowed ? 'Eligible under the experimental sharing policy. This does not guarantee authenticity.' : 'Sharing blocked: only completed, signed low-risk analyses are eligible.';
  $('share-result').replaceChildren();
}
async function history() {
  const rows = await api('/api/reports'); if (!rows.length) return;
  $('history').replaceChildren();
  rows.forEach(r => { const b = el('button', `${r.analysis.assessment} · ${r.analyzed_at.slice(0, 19)} UTC`, 'secondary'); b.onclick = async () => { try { display(await api('/api/reports/' + r.report_id)); $('results').scrollIntoView({behavior: 'smooth'}); } catch (e) { $('history').textContent = e.message; } }; $('history').append(b); });
}
$('analyze-form').onsubmit = async event => {
  event.preventDefault(); $('analyze-button').disabled = true;
  $('progress').className = 'busy'; $('progress').textContent = 'Uploading → decoding → screening faces → signing report. CPU analysis may take up to 3 minutes…';
  try { display(await api('/api/analyze', {method:'POST', body:new FormData(event.target)})); $('progress').textContent = 'Analysis complete. Review the assessment and coverage.'; await history(); }
  catch(e) { $('progress').textContent = e.message; }
  finally { $('progress').className = ''; $('analyze-button').disabled = false; }
};
$('share-button').onclick = async () => {
  try { const data = await api(`/api/reports/${current.report.report_id}/share`, {method:'POST'}); const a = el('a', location.origin + data.url); a.href = data.url; $('share-result').replaceChildren(a); }
  catch(e) { $('share-result').textContent = e.message; }
};
$('revoke-button').onclick = async () => {
  try { await api(`/api/reports/${current.report.report_id}/revoke`, {method:'POST'}); $('share-result').textContent = 'All existing links for this report are revoked.'; }
  catch(e) { $('share-result').textContent = e.message; }
};
$('download-report').onclick = () => {
  const url = URL.createObjectURL(new Blob([JSON.stringify(current.envelope, null, 2)], {type:'application/json'}));
  const a = document.createElement('a'); a.href = url; a.download = 'signed-report.json'; a.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
};
$('verify-form').onsubmit = async event => {
  event.preventDefault(); $('verification').textContent = 'Checking trusted signature and exact-file hash…';
  try { const r = await api('/api/verify', {method:'POST', body:new FormData(event.target)});
    $('verification').replaceChildren(el('p', '1. Signature: ' + r.signature_status, r.signature_valid ? '' : 'warning'), el('p', '2. Video hash: ' + (r.hash_matches ? 'Matches exact signed file' : 'MISMATCH — received bytes differ'), r.hash_matches ? '' : 'warning'), el('p', '3. Signed AI assessment: ' + (r.signed_ai_assessment || 'Unauthenticated — do not trust the claimed assessment')));
  } catch(e) { $('verification').textContent = e.message; }
};
(async () => { try {
  csrf = (await api('/api/session')).csrf_token;
  const s = await api('/api/status'); $('readiness').textContent = `${s.model_status} · Thresholds: ${s.thresholds} · Dataset evaluation: not performed`;
  $('limits').textContent = `Up to ${s.max_upload_mb} MB / ${s.max_duration_seconds} seconds · MP4 recommended · CPU`;
  await history();
} catch(e) { $('readiness').textContent = e.message; } })();
