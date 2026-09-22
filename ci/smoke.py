#!/usr/bin/env python3
"""Post-deployment smoke test.  [M04.5 - deployment validation]

"It works on my machine" is not a release.  This asserts that the thing which
just deployed is actually serving, and that it is the build we think it is.
"""
from __future__ import annotations

import sys
import time
import urllib.request
import json

ATTEMPTS = 10
PAUSE = 6


def main(base_url: str) -> int:
    url = base_url.rstrip("/") + "/healthz"
    print(f"smoke: polling {url}")

    for attempt in range(1, ATTEMPTS + 1):
        try:
            with urllib.request.urlopen(url, timeout=10) as response:
                body = json.loads(response.read())
            if response.status == 200 and body.get("status") == "ok":
                print(f"smoke: PASS - build {body.get('build')} "
                      f"in {body.get('environment')}")
                return 0
            print(f"  attempt {attempt}: unexpected body {body}")
        except Exception as error:               # noqa: BLE001 - any failure retries
            print(f"  attempt {attempt}: {type(error).__name__}")
        time.sleep(PAUSE)

    print("=" * 72)
    print("SMOKE TEST FAILED - the deployment is not serving")
    print("=" * 72)
    print("The previous version is still live; Railway does not route traffic to\n"
          "a build whose health check never passed.  Roll back by reverting the\n"
          "merge commit and pushing.")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"))
