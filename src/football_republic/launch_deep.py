"""Launch the full deep Streamlit simulation."""

from __future__ import annotations

from pathlib import Path
import sys


def main() -> None:
    try:
        from streamlit.web import cli as streamlit_cli
    except ImportError as exc:
        raise SystemExit(
            "The deep web interface is not installed. Run: "
            "python -m pip install -e '.[ui]'"
        ) from exc

    app_path = Path(__file__).with_name("political_webapp.py")
    sys.argv = [
        "streamlit",
        "run",
        str(app_path),
        "--browser.gatherUsageStats=false",
    ]
    raise SystemExit(streamlit_cli.main())


if __name__ == "__main__":
    main()
