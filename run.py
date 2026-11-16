import argparse
import threading
import webbrowser

import uvicorn

from server import create_app
from controller_profiles import default_profile_path

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="NONA local phone controller")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--profiles-file", default=str(default_profile_path()))
    args = parser.parse_args()
    app = create_app(port=args.port, profile_path=args.profiles_file)
    print(f"\nNONA dashboard: http://localhost:{args.port}\n")
    print("Connect your phone to the same Wi-Fi, then scan the dashboard QR code.")
    print("Desktop keyboard starts OFF. Stop this program with Ctrl+C.\n")
    if not args.no_browser:
        threading.Timer(1.2, lambda: webbrowser.open(f"http://localhost:{args.port}")).start()
    uvicorn.run(app, host="0.0.0.0", port=args.port, access_log=False, ws_max_size=2048,
                proxy_headers=False)
