"""Exercise the real local UI, model, signed sharing, verification and revocation."""
import base64
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.config import ROOT


def main():
    from playwright.sync_api import sync_playwright, expect
    artifacts = ROOT / 'artifacts'
    video = artifacts / 'portrait-smoke.mp4'
    if not video.exists():
        raise SystemExit('Run scripts/smoke_model.py first, then launch the local server')
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={'width': 1440, 'height': 1100})
        errors = []
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.goto('http://127.0.0.1:8000/')
        expect(page.locator('#readiness')).to_contain_text('Checkpoint checksum verified', timeout=30000)
        page.screenshot(path=str(artifacts / 'home-desktop.png'), full_page=True)
        page.locator('#video').set_input_files(str(video))
        page.locator('#analyze-button').click()
        expect(page.locator('#progress')).to_contain_text('Analysis complete', timeout=210000)
        assert page.locator('#results').inner_text().startswith('Low detected manipulation risk')
        session = page.request.get('http://127.0.0.1:8000/api/session').json()
        reports = page.request.get('http://127.0.0.1:8000/api/reports').json()
        identifier = reports[0]['report_id']
        data = page.request.get(f'http://127.0.0.1:8000/api/reports/{identifier}').json()
        report_path = artifacts / 'signed-report.json'
        report_path.write_text(json.dumps(data['envelope']))
        page.locator('#share-button').click()
        page.wait_for_selector('#share-result a')
        link = page.locator('#share-result a').get_attribute('href')
        received = page.request.get('http://127.0.0.1:8000' + link + '/video')
        assert received.status == 200 and received.body() == video.read_bytes()
        assert page.request.get('http://127.0.0.1:8000' + link).status == 200
        page.locator('#verify-form input[name=video]').set_input_files(str(video))
        page.locator('#verify-form input[name=report]').set_input_files(str(report_path))
        page.locator('#verify-form button').click()
        expect(page.locator('#verification')).to_contain_text('Matches exact signed file')
        assert 'Valid signature' in page.locator('#verification').inner_text()
        page.screenshot(path=str(artifacts / 'results-desktop.png'), full_page=True)
        modified_video = artifacts / 'modified.mp4'
        modified_video.write_bytes(video.read_bytes() + b'byte change for tampering demo')
        page.locator('#verify-form input[name=video]').set_input_files(str(modified_video))
        page.locator('#verify-form button').click()
        expect(page.locator('#verification')).to_contain_text('MISMATCH')
        assert 'Valid signature' in page.locator('#verification').inner_text()
        env = data['envelope'].copy()
        payload = json.loads(base64.b64decode(env['payload']))
        payload['analysis']['reason'] = 'Tampered reason for demo'
        env['payload'] = base64.b64encode(json.dumps(payload).encode()).decode()
        tampered = artifacts / 'tampered-report.json'
        tampered.write_text(json.dumps(env))
        page.locator('#verify-form input[name=video]').set_input_files(str(video))
        page.locator('#verify-form input[name=report]').set_input_files(str(tampered))
        page.locator('#verify-form button').click()
        expect(page.locator('#verification')).to_contain_text('Invalid signature')
        page.locator('#revoke-button').click()
        expect(page.locator('#share-result')).to_contain_text('revoked')
        for suffix in ('', '/video', '/report'):
            assert page.request.get('http://127.0.0.1:8000' + link + suffix).status == 404
        page.set_viewport_size({'width': 390, 'height': 844})
        page.screenshot(path=str(artifacts / 'results-mobile.png'), full_page=True)
        assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
        assert not errors, errors
        output = {'real_model_ui_workflow': 'passed', 'video_tampering': 'hash mismatch, signature valid',
                  'report_tampering': 'signature invalid', 'revocation': 'all three routes 404',
                  'mobile_overflow': False, 'javascript_errors': errors,
                  'model_score': data['report']['analysis']['score'],
                  'analyzed_faces': data['report']['coverage']['analyzed_faces'],
                  'fixture': 'Repeated public-domain NASA portrait, NOT detection evaluation data'}
        (artifacts / 'browser-smoke.json').write_text(json.dumps(output, indent=2))
        print(json.dumps(output, indent=2))
        browser.close()


if __name__ == '__main__':
    main()
