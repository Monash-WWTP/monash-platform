import hashlib
import json
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ROWS = json.loads((ROOT / "docs/migration/source-inventory.json").read_text())["files"]
MOBILE_ADAPTATIONS = {
    "android/gradle.properties",
    "android/app/build.gradle.kts",
    "android/app/src/debug/AndroidManifest.xml",
    "lib/config/env.dart",
    "lib/main.dart",
    "lib/models/report.dart",
    "lib/screens/map_screen.dart",
    "lib/screens/profile_screen.dart",
    "lib/screens/report_form_screen.dart",
    "lib/services/report_repository.dart",
    "lib/theme/app_theme.dart",
    "lib/widgets/category_tile.dart",
    "README.md",
    "pubspec.lock",
    "pubspec.yaml",
    "test/widgets/category_tile_test.dart",
}
DASHBOARD_ADAPTATIONS = {
    "frontend/README.md",
    "frontend/.gitignore",
    "frontend/src/api/client.ts", "frontend/src/api/monitoring.ts",
    "frontend/src/components/auth/OperatorAccess.tsx", "frontend/vite.config.ts",
    "frontend/src/lib/supabase.ts",
    "frontend/vercel.json",
    "frontend/src/main.tsx",
    "frontend/src/pages/WorkspacePage.tsx",
    "frontend/src/components/scenario/ScenarioPanel.tsx",
    "frontend/src/components/comparison/ComparisonView.tsx",
    "frontend/src/components/results/ResultsPanel.tsx",
    "frontend/src/components/ui.tsx",
    "frontend/src/index.css",
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


def test_dashboard_uses_native_versioned_api():
    client = (ROOT / "apps/dashboard/src/api/client.ts").read_text()
    monitoring = (ROOT / "apps/dashboard/src/api/monitoring.ts").read_text()
    assert "'/api/v1/plants'" in client
    assert "/api/v1/monitoring/stations" in monitoring
    assert "supabase" not in client + monitoring


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
    dependencies = (ROOT / "apps/citizenflood/pubspec.yaml").read_text()
    assert "flutter_appauth:" in dependencies and "flutter_secure_storage:" in dependencies
    assert "supabase_flutter:" not in dependencies
