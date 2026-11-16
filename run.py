import argparse
import threading
import webbrowser

import uvicorn

from server import create_app
from controller_profiles import default_profile_path
from local_tls import tls_folder

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="NONA local phone controller")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--profiles-file", default=str(default_profile_path()))
    parser.add_argument('--https', action='store_true', help='Use prepared local HTTPS certificates for motion sensors')
    parser.add_argument('--certfile', help='Use an existing trusted HTTPS certificate instead')
    parser.add_argument('--keyfile', help='Private key for --certfile')
    args = parser.parse_args()
    secure = args.https or bool(args.certfile or args.keyfile)
    certfile = args.certfile or str(tls_folder() / 'server-cert.pem')
    keyfile = args.keyfile or str(tls_folder() / 'server-key.pem')
    if secure:
        from pathlib import Path
        if not Path(certfile).is_file() or not Path(keyfile).is_file():
            parser.error('HTTPS certificate/key missing. Run PREPARE_MOTION_HTTPS.bat and read docs/MOTION_TEST.md.')
    scheme = 'https' if secure else 'http'
    app = create_app(port=args.port, profile_path=args.profiles_file, scheme=scheme,
                     tls_dir=Path(certfile).parent if secure else None)
    print(f"\nNONA dashboard: {scheme}://localhost:{args.port}\n")
    print("Connect your phone to the same Wi-Fi, then scan the dashboard QR code.")
    print("Desktop keyboard starts OFF. Stop this program with Ctrl+C.\n")
    if not args.no_browser:
        threading.Timer(1.2, lambda: webbrowser.open(f"{scheme}://localhost:{args.port}")).start()
    uvicorn.run(app, host="0.0.0.0", port=args.port, access_log=False, ws_max_size=2048,
                proxy_headers=False, ssl_certfile=certfile if secure else None, ssl_keyfile=keyfile if secure else None)
