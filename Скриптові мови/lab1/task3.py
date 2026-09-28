import csv
import datetime
import functools
import hashlib
import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))
from shared.student import STUDENT_NAME, VARIANT_NUMBER

DATA_DIR = Path(__file__).resolve().parent / "data"
USERS_CSV = DATA_DIR / "users.csv"
LOG_JSON = DATA_DIR / "log.json"

MIN_PASSWORD_LENGTH = 15

class ValidationError(Exception):
    pass

def generate_hash(password: str, salt: str = "00000") -> str:
    if not password or not salt:
        raise ValueError("Пароль та сіль не можуть бути порожніми")

    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValidationError(
            f"Пароль закороткий (мінімум {MIN_PASSWORD_LENGTH} символів)"
        )

    combined = (password + salt).encode("utf-8")
    return hashlib.sha384(combined).hexdigest()


def log_event(func):
    @functools.wraps(func)
    def wrapper(username: str, password: str, *args, **kwargs):
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        res_status = "failure"
        try:
            success = func(username, password, *args, **kwargs)
            res_status = "success" if success else "failure"
            return success
        finally:
            log_entry = {
                "event": "login",
                "user": username,
                "result": res_status,
                "timestamp": now,
                "args": [username],
                "kwargs": {},
            }
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            logs = []
            if LOG_JSON.exists():
                try:
                    with open(LOG_JSON, "r", encoding="utf-8") as f:
                        logs = json.load(f)
                except (json.JSONDecodeError, IOError):
                    logs = []

            logs.append(log_entry)
            with open(LOG_JSON, "w", encoding="utf-8") as f:
                json.dump(logs, f, indent=4, ensure_ascii=False)

    return wrapper

def create_user(username: str, password: str, salt: str) -> tuple[str, str]:
    return username, generate_hash(password, salt)


def create_users(users_list: tuple[tuple[str, str], ...], salt: str) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(USERS_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["username", "password_hash"])
        for user, pwd in users_list:
            try:
                u, h = create_user(user, pwd, salt)
                writer.writerow([u, h])
            except (ValueError, ValidationError) as err:
                print(f"[Помилка створення {user}]: {err}")


def read_users_db() -> list[dict[str, str]]:
    if not USERS_CSV.exists():
        raise FileNotFoundError(f"Файл {USERS_CSV} не знайдено.")

    users = []
    with open(USERS_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            users.append(row)
    return users


@log_event
def login(username: str, password: str, salt: str) -> bool:
    if not username or not password:
        raise ValueError("Логін і пароль є обов'язковими для входу")

    db = read_users_db()
    for record in db:
        if record["username"] == username:
            computed_hash = generate_hash(password, salt)
            return computed_hash == record["password_hash"]
    return False

def run_task3() -> None:
    print("=" * 60)
    print(f"Завдання 3 | Студент: {STUDENT_NAME} | Варіант: {VARIANT_NUMBER}")
    print("=" * 60)

    salt = f"{VARIANT_NUMBER:05d}"

    users_to_register = (
        ("admin_sec", "SuperSecurePass_2026!"),
        ("analyst_01", "ThreatHunterPass#99"),
        ("net_eng", "CiscoPacketTracer!1"),
        ("dev_sec", "CSharpUnityLiminal!"),
        ("crypto_user", "GothTownPurpleGate#"),
        ("incident_resp", "CSIRTEmergency2026$"),
        ("auditor", "ComplianceReport*88"),
        ("soc_lead", "MonitoringCenter#1"),
        ("guest_temp", "TemporaryAccess2026@"),
        ("bad_pass_user", "short"),
    )

    print(f"[*] Створення CSV бази з сіллю: '{salt}'...")
    create_users(users_to_register, salt)

    print("\n[*] Зміст бази даних users.csv:")
    try:
        db = read_users_db()
        print(f"{'Username':<15} | {'SHA384 Hash (перші 25 символів)':<30}")
        print("-" * 50)
        for rec in db:
            print(f"{rec['username']:<15} | {rec['password_hash'][:25]}...")
    except (FileNotFoundError, PermissionError, IOError) as e:
        print(f"[Помилка читання БД]: {e}")

    print("\n[*] Тестування автентифікації та логування:")
    test_cases = [
        ("admin_sec", "SuperSecurePass_2026!"),  # Успішний вхід
        ("analyst_01", "WrongPasswordHere!"),  # Неправильний пароль
        ("unknown_hacker", "RandomPass1234567!"),  # Неіснуючий юзер
    ]

    for u, p in test_cases:
        try:
            res = login(u, p, salt)
            status = "Вхід успішний" if res else "Помилка автентифікації"
            print(f" - Вхід користувача '{u}': {status}")
        except (ValueError, ValidationError, IOError) as err:
            print(f" - [Помилка для '{u}']: {err}")

    if LOG_JSON.exists():
        print(f"\n[+] Спроби залоговано у {LOG_JSON.name}")


if __name__ == "__main__":
    run_task3()