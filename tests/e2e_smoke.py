import os
import sys
from playwright.sync_api import sync_playwright

def test_e2e_smoke():
    screenshot_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "docs", "screenshots")
    os.makedirs(screenshot_dir, exist_ok=True)
    screenshot_path = os.path.join(screenshot_dir, "e2e_results.png")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 900})
        page = context.new_page()

        # 1. Buka halaman utama
        page.goto("http://127.0.0.1:8000", wait_until="networkidle")
        page.wait_for_selector('[data-action="load-sample-tender"]', state="visible", timeout=10000)

        # 2. Klik "Coba dengan contoh"
        page.click('[data-action="load-sample-tender"]')

        # 3. Dialog audit terbuka dengan data terisi
        page.wait_for_selector("#audit-dialog[open]", state="visible", timeout=5000)
        page.wait_for_selector("#submit-audit", state="visible", timeout=5000)

        # 4. Klik "Jalankan evaluasi"
        page.click("#submit-audit")

        # 5. Tunggu proses evaluasi selesai dan dialog tertutup
        page.wait_for_selector("#audit-dialog[open]", state="detached", timeout=15000)

        # 6. Pastikan tab berpindah ke hasil evaluasi & tabel temuan muncul dan terisi
        page.wait_for_selector("#risk-review", state="visible", timeout=10000)
        page.wait_for_selector(".review-table tbody tr.review-row", state="visible", timeout=10000)

        rows = page.query_selector_all(".review-table tbody tr.review-row")
        assert len(rows) > 0, "Tabel temuan evaluasi harus terisi minimal 1 baris"

        # Verifikasi verdict terlihat
        verdict_el = page.query_selector(".eligibility-badge")
        assert verdict_el is not None, "Badge verdict harus tampil"
        verdict_text = verdict_el.inner_text().strip()
        assert verdict_text in ("NO-GO", "REVIEW", "BELUM CUKUP BUKTI", "GO"), f"Verdict tidak valid: {verdict_text}"

        # 7. Simpan screenshot hasil di docs/screenshots/e2e_results.png
        page.screenshot(path=screenshot_path, full_page=True)
        assert os.path.exists(screenshot_path), f"Screenshot harus ada di {screenshot_path}"
        assert os.path.getsize(screenshot_path) > 1000, "Screenshot file tidak boleh kosong"

        browser.close()

if __name__ == "__main__":
    test_e2e_smoke()
    print("E2E smoke test passed successfully! Screenshot saved to docs/screenshots/e2e_results.png")
