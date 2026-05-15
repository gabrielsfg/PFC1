import base64
import zlib
from pathlib import Path

import requests

_KROKI_URL = "https://kroki.io/plantuml/png"
_TIMEOUT = 30


class KrokiClient:
    """Renders PlantUML diagrams to PNG via the kroki.io public API."""

    def render(self, plantuml_source: str, output_path: Path) -> Path:
        png_bytes = self._fetch_png(plantuml_source)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(png_bytes)
        return output_path

    def _fetch_png(self, source: str) -> bytes:
        encoded = _encode(source)
        response = requests.get(f"{_KROKI_URL}/{encoded}", timeout=_TIMEOUT)
        response.raise_for_status()
        return response.content


def _encode(source: str) -> str:
    compressed = zlib.compress(source.encode("utf-8"), level=9)
    return base64.urlsafe_b64encode(compressed).decode("ascii")
