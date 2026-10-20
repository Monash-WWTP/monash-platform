"""Guard the Android task configuration required by the AppAuth callback."""
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
ANDROID = "{http://schemas.android.com/apk/res/android}"


def test_mobile_auth_callback_keeps_application_task_affinity():
    manifest = ROOT / "apps/citizenflood/android/app/src/main/AndroidManifest.xml"
    main = ET.parse(manifest).find("./application/activity")
    assert main is not None
    # AppAuth's management activity must resume with its original authorization state.
    assert main.get(f"{ANDROID}taskAffinity") != ""
