import hashlib
import json
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ROWS = json.loads((ROOT / "docs/migration/source-inventory.json").read_text())["files"]
MOBILE_ADAPTATIONS = {"android/gradle.properties", "README.md"}
DASHBOARD_ADAPTATIONS = {
    "frontend/README.md",
    "frontend/src/main.tsx",
    "frontend/src/pages/WorkspacePage.tsx",
    "frontend/package.json",
    "frontend/package-lock.json",
    "frontend/src/pages/MapPage.tsx",
    "frontend/src/components/comparison/ComparisonView.tsx",
    "frontend/src/components/dashboard/TrendsChart.tsx",
    "frontend/src/components/monitoring/StationDashboard.tsx",
    "frontend/src/components/twin/DigitalTwin.tsx",
    "frontend/src/components/ui.tsx",
    "frontend/src/components/ui/badge.tsx",
    "frontend/src/components/ui/button.tsx",
    "frontend/src/components/ui/tabs.tsx",
}


def test_mobile_documented_launcher_is_executable():
    assert os.access(ROOT / "apps/citizenflood/scripts/run.sh", os.X_OK), "documented launcher must execute on a fresh checkout"


def test_dashboard_snapshot_matches_pinned_frontend():
    rows = [r for r in ROWS if r["source_repo"] == "dashboard" and
            r["source_path"].startswith("frontend/")]
    assert rows
    for row in rows:
        target = ROOT / row["target_path"]
        assert target.is_file(), str(target)
        if row["source_path"] not in DASHBOARD_ADAPTATIONS:
            assert hashlib.sha256(target.read_bytes()).hexdigest() == row["source_sha256"]
    assert {r["source_path"] for r in rows if
            hashlib.sha256((ROOT / r["target_path"]).read_bytes()).hexdigest()
            != r["source_sha256"]} == DASHBOARD_ADAPTATIONS


def test_dashboard_import_keeps_legacy_data_routes():
    client = (ROOT / "apps/dashboard/src/api/client.ts").read_text()
    monitoring = (ROOT / "apps/dashboard/src/api/monitoring.ts").read_text()
    assert "'/api/plants'" in client
    assert "supabase.from('stations')" in monitoring
    assert "'/api/v1/" not in client


def test_citizenflood_snapshot_matches_pinned_app():
    rows = [r for r in ROWS if r["source_repo"] == "citizenflood" and
            r["disposition"] == "imported"]
    assert rows
    for row in rows:
        target = ROOT / row["target_path"]
        assert target.is_file(), str(target)
        if row["source_path"] not in MOBILE_ADAPTATIONS:
            assert hashlib.sha256(target.read_bytes()).hexdigest() == row["source_sha256"]
    assert {r["source_path"] for r in rows if
            hashlib.sha256((ROOT / r["target_path"]).read_bytes()).hexdigest()
            != r["source_sha256"]} == MOBILE_ADAPTATIONS
    lock = ROOT / "apps/citizenflood/pubspec.lock"
    assert hashlib.sha256(lock.read_bytes()).hexdigest() == next(
        r["source_sha256"] for r in rows if r["source_path"] == "pubspec.lock"
    )
