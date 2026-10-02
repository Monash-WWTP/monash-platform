"""Write the reviewed OpenAPI contract deterministically."""

import json
from pathlib import Path

from app.main import app


OUTPUT = Path(__file__).resolve().parents[1] / "services" / "api" / "openapi.json"


def main() -> None:
    OUTPUT.write_text(json.dumps(app.openapi(), indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
