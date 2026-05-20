import psutil
import logging
import time
import os

# ── Thresholds (edit these as needed) ──
THRESHOLDS = {
    "cpu_percent":    80.0,
    "memory_percent": 80.0,
    "disk_percent":   85.0,
    "process_count":  300,
}

CHECK_INTERVAL = 10   # seconds between checks (0 = run once and exit)
LOG_FILE = "health_monitor.log"
# ────────────────────────────────────────

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


def check_cpu():
    cpu = psutil.cpu_percent(interval=1)
    status = "ALERT" if cpu > THRESHOLDS["cpu_percent"] else "OK"
    return {"metric": "CPU Usage", "value": cpu, "unit": "%",
            "threshold": THRESHOLDS["cpu_percent"], "status": status}


def check_memory():
    mem = psutil.virtual_memory()
    status = "ALERT" if mem.percent > THRESHOLDS["memory_percent"] else "OK"
    return {"metric": "Memory Usage", "value": round(mem.percent, 1), "unit": "%",
            "threshold": THRESHOLDS["memory_percent"], "status": status,
            "used_gb": round(mem.used / (1024**3), 2),
            "total_gb": round(mem.total / (1024**3), 2)}


def check_disk(path="/"):
    disk = psutil.disk_usage(path)
    status = "ALERT" if disk.percent > THRESHOLDS["disk_percent"] else "OK"
    return {"metric": f"Disk Usage ({path})", "value": disk.percent, "unit": "%",
            "threshold": THRESHOLDS["disk_percent"], "status": status,
            "used_gb": round(disk.used / (1024**3), 2),
            "total_gb": round(disk.total / (1024**3), 2)}


def check_processes():
    count = len(psutil.pids())
    status = "ALERT" if count > THRESHOLDS["process_count"] else "OK"
    return {"metric": "Running Processes", "value": count, "unit": " procs",
            "threshold": THRESHOLDS["process_count"], "status": status}


def run_checks():
    results = [check_cpu(), check_memory(), check_disk("/"), check_processes()]
    alerts = [r for r in results if r["status"] == "ALERT"]

    logger.info("=" * 55)
    logger.info("  SYSTEM HEALTH CHECK")
    logger.info("=" * 55)

    for r in results:
        icon = "ALERT" if r["status"] == "ALERT" else "OK   "
        msg = f"[{icon}] {r['metric']:<25} {r['value']}{r['unit']} (limit: {r['threshold']}{r['unit']})"
        if r["status"] == "ALERT":
            logger.warning(msg)
        else:
            logger.info(msg)

    if alerts:
        logger.warning(f"  {len(alerts)} ALERT(S) DETECTED!")
    else:
        logger.info("  All metrics within normal range.")
    logger.info("=" * 55)
    return alerts


def main():
    logger.info(f"Health Monitor started. Logging to: {os.path.abspath(LOG_FILE)}")
    if CHECK_INTERVAL == 0:
        run_checks()
    else:
        logger.info(f"Checking every {CHECK_INTERVAL}s. Ctrl+C to stop.")
        try:
            while True:
                run_checks()
                time.sleep(CHECK_INTERVAL)
        except KeyboardInterrupt:
            logger.info("Monitor stopped.")


if __name__ == "__main__":
    main()
