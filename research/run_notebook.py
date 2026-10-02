"""Execute the committed exploratory notebook against the local data snapshot."""
import json
import os
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")
root = Path(__file__).resolve().parents[1]
os.chdir(root)
notebook = json.loads((root / "research/notebooks/wwtp_explore.ipynb").read_text())
namespace = {"__name__": "__main__"}
for index, cell in enumerate(notebook["cells"]):
    if cell["cell_type"] == "code":
        exec(compile("".join(cell["source"]), f"wwtp_explore.ipynb:cell-{index}", "exec"), namespace)
print(f"Notebook completed: {len(namespace['samples'])} final-effluent samples, snapshot {namespace['manifest']['version']}")
