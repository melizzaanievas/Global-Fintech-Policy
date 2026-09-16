import os
import sys
import traceback

import requests

GOOD_MAIN_URL = (
    "https://raw.githubusercontent.com/melizzaanievas/Global-Fintech-Policy/"
    "70907d1d149d303fb19366e2302f467deaab5515/main.py"
)
FALLBACK_MAIN_URL = (
    "https://raw.githubusercontent.com/melizzaanievas/Global-Fintech-Policy/"
    "13397710d3d5beb7fec26beca2ba04ba5349764c/main.py"
)


def load_known_good_main():
    """Load the last known-good app source from the repository history."""
    urls = [GOOD_MAIN_URL, FALLBACK_MAIN_URL]
    last_error = None

    for url in urls:
        try:
            response = requests.get(url, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
            response.raise_for_status()
            source = response.text
            if not source.strip():
                raise ValueError("Downloaded source is empty")
            namespace = {"__name__": "__main__", "__file__": __file__}
            exec(compile(source, str(__file__), "exec"), namespace, namespace)
            return
        except Exception as exc:  # pragma: no cover - runtime fallback only
            last_error = exc

    raise RuntimeError(
        "Failed to load the last known-good main.py from git history. "
        f"Tried: {urls}. Last error: {last_error}"
    )


if __name__ == "__main__":
    try:
        load_known_good_main()
    except Exception:
        traceback.print_exc()
        print(
            "\nStreamlit app startup failed because the app source in this file was replaced "
            "with a placeholder. The bootstrap loader could not fetch the last known-good "
            "main.py from Git history. Restore the repo source manually and redeploy."
        )
        raise
