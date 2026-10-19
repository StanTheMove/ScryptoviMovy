import argparse
import csv
import json
import logging
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

CRITICAL_KEYWORDS = ("secrets", "payroll", "admin", "budget")


@dataclass
class ActivityRecord:
    timestamp: datetime
    user_id: str
    action: str
    resource: str
    ip: str


def setup_logger(log_file: Path | None = None) -> logging.Logger:
    logger = logging.getLogger("UserActivityAudit")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    formatter = logging.Formatter("[%(levelname)s] %(message)s")

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def parse_activity_log(file_path: Path) -> list[ActivityRecord]:
    if not file_path.exists():
        raise FileNotFoundError(f"Файл логів не знайдено: {file_path}")

    records: list[ActivityRecord] = []
    with file_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append(
                ActivityRecord(
                    timestamp=datetime.fromisoformat(row["Timestamp"]),
                    user_id=row["UserID"],
                    action=row["Action"],
                    resource=row["Resource"],
                    ip=row["IP"],
                )
            )
    return records


def analyze_activities(
    records: list[ActivityRecord],
    logger: logging.Logger,
    check_after_hours: bool = True,
) -> dict:
    total_records = len(records)
    logger.info(f"Total records processed: {total_records}.")

    off_hours_alerts = []
    critical_access_by_user = defaultdict(list)

    for r in records:
        is_weekend = r.timestamp.weekday() >= 5
        is_night = r.timestamp.hour >= 22 or r.timestamp.hour < 6

        if check_after_hours and (is_weekend or is_night):
            reason = "Weekend" if is_weekend else "Night"
            off_hours_alerts.append(
                {
                    "user_id": r.user_id,
                    "action": r.action,
                    "resource": r.resource,
                    "ip": r.ip,
                    "timestamp": r.timestamp.isoformat(),
                    "reason": reason,
                }
            )

        if any(keyword in r.resource.lower() for keyword in CRITICAL_KEYWORDS):
            critical_access_by_user[r.user_id].append(r)

    if off_hours_alerts:
        print("\n=== Off-Hours Activity Alerts (22:00 - 06:00 / Weekends) ===")
        for alert in off_hours_alerts:
            time_str = alert["timestamp"]
            msg = (
                f"User '{alert['user_id']}' performed {alert['action']} at"
                f" {time_str} (Resource: {alert['resource']}, Reason:"
                f" {alert['reason']}) from IP {alert['ip']}"
            )
            logger.warning(msg)

    mass_anomalies = []
    print("\n=== Critical Resource Access Anomalies ===")
    for user_id, actions in critical_access_by_user.items():
        if len(actions) >= 5:
            msg = (
                f"User '{user_id}' executed {len(actions)} suspicious actions on"
                f" critical resources from IP {actions[0].ip}."
            )
            logger.warning(msg)
            mass_anomalies.append(
                {
                    "user_id": user_id,
                    "actions_count": len(actions),
                    "ip": actions[0].ip,
                    "targeted_resources": list({a.resource for a in actions}),
                }
            )

    report = {
        "total_records": total_records,
        "off_hours_count": len(off_hours_alerts),
        "off_hours_alerts": off_hours_alerts,
        "critical_access_anomalies": mass_anomalies,
    }
    return report


def main():
    parser = argparse.ArgumentParser(description="User Activity Audit CLI (Variant 7)")
    parser.add_argument(
        "--activity-log",
        type=Path,
        required=True,
        help="Шлях до CSV файлу активності",
    )
    parser.add_argument(
        "--after-hours",
        action="store_true",
        default=True,
        help="Перевіряти активність у позаробочий час",
    )
    parser.add_argument("--out-report", type=Path, help="Шлях до вихідного JSON-звіту")
    parser.add_argument("--log-file", type=Path, help="Шлях до файлу журналу логів")

    args = parser.parse_args()

    logger = setup_logger(args.log_file)
    logger.info(f"Reading user activity log {args.activity_log}...")

    try:
        records = parse_activity_log(args.activity_log)
        report = analyze_activities(records, logger, args.after_hours)

        if args.out_report:
            args.out_report.parent.mkdir(parents=True, exist_ok=True)
            with args.out_report.open("w", encoding="utf-8") as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            logger.info(f"Anomalous activity report written to {args.out_report}")

    except (FileNotFoundError, ValueError, csv.Error, OSError) as e:
        logger.error(f"Помилка під час аналізу: {e}")


if __name__ == "__main__":
    main()
