import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[2])),
from shared.student import STUDENT_NAME, GROUP_NAME, VARIANT_NUMBER

USERS = {
 "incident_commander": {"role": "incident_response", "clearance": 4,
"department": "CSIRT", "active": True},
 "malware_analyst": {"role": "malware_researcher", "clearance": 3,
"department": "Research", "active": True},
 "monitoring_tech": {"role": "monitoring", "clearance": 2, "department":
"NOC", "active": True},
 "customer_rep": {"role": "customer_service", "clearance": 1, "department":
"Customer", "active": True},
 "backup_service": {"role": "service_account", "clearance": 2, "department":
"System", "active": False}
}

RESOURCES = [("incident_playbook", 4), ("malware_lab", 3),
("monitoring_dashboards", 2), ("customer_portal", 1), ("emergency_procedures",
4), ("service_desk", 1), ("reverse_engineering", 3), ("alert_systems", 2),
("escalation_matrix", 3), ("knowledge_base", 1)]

SECURITY_LEVELS = ("Public Access", "Authorized", "Privileged", "Critical")

BLOCKED_USERS = {"backup_service", "deactivated_svc", "policy_violation"}

def print_resources() -> None:
    print("Список ресурсів системи:")
    for res_name, level in RESOURCES:
        text_level = SECURITY_LEVELS[level - 1]
        print(f" - {res_name:<25} [Рівень {level}: {text_level}]")
    print("-" * 60)


def check_access(username: str, resource: tuple[str, int]) -> tuple[str, str]:
    res_name, res_level = resource

    if username not in USERS:
        return "DENY", "User not found"

    if username in BLOCKED_USERS:
        return "DENY", "User is blocked"

    user_info = USERS[username]
    if not user_info.get("active", False):
        return "DENY", "Account inactive"

    if user_info.get("clearance", 0) >= res_level:
        return "ALLOW", ""

    return "DENY", "Insufficient clearance"

def run_task2() -> None:
    print("=" * 60)
    print(f"Завдання 2 | Студент: {STUDENT_NAME} | Варіант: {VARIANT_NUMBER}")
    print("=" * 60)

    print_resources()

    test_users = list(USERS.keys()) + ["unknown_intruder"]
    for user in test_users:
        for resource in RESOURCES:
            status, reason = check_access(user, resource)
            reason_str = f" ({reason})" if reason else ""
            print(
                f"user={user:<20} resource={resource[0]:<22} -> {status}{reason_str}"
            )

if __name__ == "__main__":
    run_task2()