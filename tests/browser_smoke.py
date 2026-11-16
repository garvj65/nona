"""Rendered desktop + Android-emulated racing test, run in CI or locally."""
import json
import socket
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import uvicorn
from playwright.sync_api import sync_playwright
from server import create_app


def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('127.0.0.1', 0)); sock.listen(10)
    port = sock.getsockname()[1]
    origin = f'http://127.0.0.1:{port}'
    app = create_app(port=port, addresses={'127.0.0.1', 'localhost', '192.168.1.10'})
    service = uvicorn.Server(uvicorn.Config(app, log_level='error', access_log=False, proxy_headers=False))
    thread = threading.Thread(target=lambda: service.run(sockets=[sock]), daemon=True)
    thread.start()
    deadline = time.monotonic() + 10
    while not service.started:
        if time.monotonic() > deadline: raise RuntimeError('Test server did not start')
        time.sleep(.02)
    artifacts = ROOT / 'artifacts'; artifacts.mkdir(exist_ok=True)
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            desktop = browser.new_context(viewport={'width': 1440, 'height': 1080})
            dashboard = desktop.new_page(); errors = []
            dashboard.on('pageerror', lambda error: errors.append(str(error)))
            dashboard.goto(origin, wait_until='networkidle')
            session = dashboard.request.get(origin + '/api/session').json()
            assert dashboard.locator('#qr').evaluate('(el)=>el.complete && el.naturalWidth>0')
            game = desktop.new_page(); game.on('pageerror', lambda error: errors.append(str(error)))
            game.goto(origin + '/race', wait_until='networkidle')
            android = browser.new_context(**p.devices['Pixel 7'])
            phone = android.new_page(); phone.on('pageerror', lambda error: errors.append(str(error)))
            phone.goto(origin + '/controller#' + app.state.room.token, wait_until='networkidle')
            phone.wait_for_function("document.getElementById('status').textContent==='Connected'")
            phone.locator('#controller-profile').select_option('racing_arrows')
            phone.locator('#racing-controls').wait_for(state='visible')
            dashboard.wait_for_function("document.getElementById('profile').value==='racing_arrows'")
            assert phone.evaluate('document.documentElement.scrollWidth<=innerWidth')
            phone.screenshot(path=str(artifacts / 'controller-portrait.png'), full_page=True)
            # A real touch-down and touch-up must not be lost between animation frames.
            phone.locator('[data-button=start]').tap()
            game.wait_for_function('race.running && !race.paused')
            cdp = android.new_cdp_session(phone)

            def point(selector, ident, offset=0):
                rect = phone.locator(selector).bounding_box()
                return {'x': rect['x'] + rect['width'] / 2 + offset,
                        'y': rect['y'] + rect['height'] / 2, 'id': ident}

            points = [point('#wheel', 1, 35), point('#racing-controls [data-button=a]', 2)]
            cdp.send('Input.dispatchTouchEvent', {'type': 'touchStart', 'touchPoints': points})
            game.wait_for_function("remote.has('a') && remoteSteering > 0.2")
            phone.wait_for_timeout(300)
            assert game.evaluate('race.speed > 20 && race.x > 600 && race.heading > 0')
            cdp.send('Input.dispatchTouchEvent', {'type': 'touchEnd', 'touchPoints': []})
            game.wait_for_function('remoteSteering===0 && remote.size===0')
            phone.locator('[data-button=start]').tap(); game.wait_for_function('race.paused')
            phone.locator('[data-button=start]').tap(); game.wait_for_function('!race.paused')
            phone.set_viewport_size({'width': 851, 'height': 393})
            phone.wait_for_timeout(150)
            assert phone.evaluate('document.documentElement.scrollWidth<=innerWidth')
            release = phone.locator('#release').bounding_box()
            assert release['y'] + release['height'] <= 393, release
            phone.screenshot(path=str(artifacts / 'controller-landscape.png'), full_page=True)
            game.screenshot(path=str(artifacts / 'race.png'), full_page=True)
            # Saving a custom mapping reaches the server; selecting a preset restores it.
            dashboard.locator('#mapping-editor summary').click()
            dashboard.locator('[data-action=nitro]').select_option('ctrl')
            with dashboard.expect_response(lambda response: response.url.endswith('/api/mapping')
                                           and response.request.method == 'POST') as saved:
                dashboard.locator('#save-mapping').click()
            assert saved.value.status == 200
            dashboard.wait_for_function("document.querySelector('[data-action=nitro]').value==='ctrl'")
            assert dashboard.request.get(origin + '/api/session').json()['mapping']['nitro'] == 'ctrl'
            phone.close(); game.wait_for_function('race.paused && !connected')
            assert not errors, errors
            print(json.dumps({'dashboard_and_qr': 'passed', 'profile_sync': 'passed',
                              'android_emulated_multi_touch_racing': 'passed', 'wheel_centring': 'passed',
                              'short_tap_pause_resume': 'passed', 'portrait_landscape_overflow': 'passed',
                              'custom_mapping': 'passed', 'disconnect_pause': 'passed', 'page_errors': errors}))
            android.close(); desktop.close(); browser.close()
    finally:
        service.should_exit = True; thread.join(timeout=5); sock.close()


if __name__ == '__main__':
    main()
