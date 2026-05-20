import requests
import logging
import time
import sys
import os

# ── Target URLs to monitor ──
TARGETS = [
    {"name": "Wisecow App",     "url": "http://wisecow.local"},
    {"name": "Google (sanity)", "url": "https://www.google.com"},
]

TIMEOUT_SECONDS = 5
CHECK_INTERVAL  = 30   # seconds (0 = run once and exit)
LOG_FILE        = "app_health.log"
# ────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

HEALTHY_CODES = range(200, 400)


def check_url(target):
    name = target["name"]
    url  = target["url"]
    result = {"name": name, "url": url, "status": None,
              "http_code": None, "response_ms": None, "error": None}
    try:
        start   = time.time()
        resp    = requests.get(url, timeout=TIMEOUT_SECONDS, allow_redirects=True)
        elapsed = round((time.time() - start) * 1000, 1)
        result["http_code"]   = resp.status_code
        result["response_ms"] = elapsed
        result["status"]      = "UP" if resp.status_code in HEALTHY_CODES else "DOWN"
    except requests.exceptions.ConnectionError:
        result["status"] = "DOWN"
        result["error"]  = "Connection refused / DNS failure"
    except requests.exceptions.Timeout:
        result["status"] = "DOWN"
        result["error"]  = f"Timed out after {TIMEOUT_SECONDS}s"
    except requests.exceptions.RequestException as e:
        result["status"] = "DOWN"
        result["error"]  = str(e)
    return result


def print_report(results):
    logger.info("=" * 65)
    logger.info("  APPLICATION HEALTH REPORT")
    logger.info("=" * 65)
    up_count   = sum(1 for r in results if r["status"] == "UP")
    down_count = len(results) - up_count
    for r in results:
        if r["status"] == "UP":
            logger.info(f"  [UP]   {r['name']:<22} HTTP {r['http_code']} | {r['response_ms']}ms")
        else:
            reason = f"HTTP {r['http_code']}" if r["http_code"] else r["error"]
            logger.warning(f"  [DOWN] {r['name']:<22} {reason}")
    logger.info("-" * 65)
    logger.info(f"  Summary: {up_count} UP | {down_count} DOWN | {len(results)} total")
    logger.info("=" * 65)


def main():
    logger.info(f"App Health Checker started. Log: {os.path.abspath(LOG_FILE)}")
    if len(sys.argv) > 1:
        TARGETS.clear()
        for url in sys.argv[1:]:
            TARGETS.append({"name": url, "url": url})
    if CHECK_INTERVAL == 0:
        print_report([check_url(t) for t in TARGETS])
    else:
        logger.info(f"Checking every {CHECK_INTERVAL}s. Ctrl+C to stop.")
        try:
            while True:
                print_report([check_url(t) for t in TARGETS])
                time.sleep(CHECK_INTERVAL)
        except KeyboardInterrupt:
            logger.info("Checker stopped.")


if __name__ == "__main__":
    main()
