import os
import sys
import json
import logging
from pathlib import Path
from starlette.testclient import TestClient

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.app.main import app
from backend.app.config import BASE_DIR, FRONTEND_DIST, TEMP_DIR

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_frontend_and_api_audit():
    print("=" * 60)
    print("AUDIT SECTION 5: FRONTEND ARCHITECTURE & BACKEND API VERIFICATION")
    print("=" * 60)

    client = TestClient(app)
    results = {
        "frontend_source_structure": {},
        "api_endpoints": {},
        "upload_test": {},
        "url_test": {},
        "error_handling": {}
    }

    # 1. Verify React Source vs Dist Structure
    frontend_dir = BASE_DIR / "frontend"
    src_dir = frontend_dir / "src"
    dist_dir = frontend_dir / "dist"

    src_files = list(src_dir.rglob("*.jsx")) + list(src_dir.rglob("*.js")) + list(src_dir.rglob("*.css"))
    dist_files = list(dist_dir.rglob("*.*"))

    results["frontend_source_structure"] = {
        "src_directory_exists": src_dir.exists(),
        "src_files_count": len(src_files),
        "src_files": [f.name for f in src_files],
        "dist_directory_exists": dist_dir.exists(),
        "dist_files": [f.name for f in dist_files],
        "is_dist_standalone": (dist_dir / "index.html").exists()
    }

    print("\n[1] Frontend Code Structure Inspection:")
    print(f"  - React 'frontend/src/' directory exists: {src_dir.exists()} ({len(src_files)} files)")
    print(f"  - Components present: {[f.name for f in src_files if 'components' in str(f)]}")
    print(f"  - Production 'frontend/dist/' exists: {dist_dir.exists()} (index.html: {(dist_dir / 'index.html').exists()})")

    # 2. Test Root HTML Delivery
    res_root = client.get("/")
    has_root = 'id="root"' in res_root.text
    results["api_endpoints"]["root_spa"] = {
        "status_code": res_root.status_code,
        "content_type": res_root.headers.get("content-type"),
        "has_react_root": has_root
    }
    print(f"\n[2] Frontend Serving: Status {res_root.status_code} | Has React Root: {has_root}")

    # 3. Test System Diagnostics API
    res_sys = client.get("/api/system")
    sys_data = res_sys.json() if res_sys.status_code == 200 else {}
    results["api_endpoints"]["system_diagnostics"] = {
        "status_code": res_sys.status_code,
        "ffmpeg_available": sys_data.get("ffmpeg_available"),
        "ytdlp_available": sys_data.get("ytdlp_available"),
        "temp_free_gb": sys_data.get("temp_disk_free_gb")
    }
    print(f"\n[3] System Diagnostics (/api/system):")
    print(f"  - FFmpeg: {sys_data.get('ffmpeg_available')} ({sys_data.get('ffmpeg_path')})")
    print(f"  - yt-dlp: {sys_data.get('ytdlp_available')}")
    print(f"  - Temp Disk Free: {sys_data.get('temp_disk_free_gb')} GB")

    # 4. Test URL Ingestion Endpoint
    payload = {
        "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "aspect_ratio": "9:16",
        "subtitle_style": "hormozi",
        "min_duration": 20,
        "max_duration": 60,
        "max_clips": 3
    }
    res_url = client.post("/api/process-url", json=payload)
    url_job = res_url.json() if res_url.status_code == 200 else {}
    results["url_test"] = {
        "status_code": res_url.status_code,
        "job_id": url_job.get("job_id"),
        "status": url_job.get("status")
    }
    print(f"\n[4] URL Submission (/api/process-url):")
    print(f"  - Status Code: {res_url.status_code} | Job ID: {url_job.get('job_id')} | Status: {url_job.get('status')}")

    # 5. Test File Upload Endpoint
    dummy_file_path = TEMP_DIR / "audit_test_upload.mp4"
    dummy_file_path.write_bytes(b"\x00" * 4096)  # 4KB dummy file

    with open(dummy_file_path, "rb") as f:
        res_upload = client.post(
            "/api/upload",
            files={"file": ("test_video.mp4", f, "video/mp4")},
            data={
                "aspect_ratio": "9:16",
                "subtitle_style": "hormozi",
                "min_duration": 10,
                "max_duration": 30,
                "max_clips": 2
            }
        )
    upload_job = res_upload.json() if res_upload.status_code == 200 else {}
    results["upload_test"] = {
        "status_code": res_upload.status_code,
        "job_id": upload_job.get("job_id"),
        "status": upload_job.get("status")
    }
    print(f"\n[5] Video File Upload (/api/upload):")
    print(f"  - Status Code: {res_upload.status_code} | Job ID: {upload_job.get('job_id')}")

    if dummy_file_path.exists():
        dummy_file_path.unlink()

    # 6. Test Error Handling
    res_invalid_job = client.get("/api/jobs/nonexistent_id_404")
    res_empty_url = client.post("/api/process-url", json={"url": ""})
    results["error_handling"] = {
        "nonexistent_job_404": res_invalid_job.status_code == 404,
        "empty_url_rejected": res_empty_url.status_code in (400, 422)
    }
    print(f"\n[6] Error Handling Resilience:")
    print(f"  - Missing job returns 404: {res_invalid_job.status_code == 404}")
    print(f"  - Invalid URL rejected: {res_empty_url.status_code in (400, 422)}")

    report_path = Path(__file__).parent / "frontend_api_audit_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\n[+] Frontend & API audit report saved to {report_path}")
    return results

if __name__ == "__main__":
    run_frontend_and_api_audit()
