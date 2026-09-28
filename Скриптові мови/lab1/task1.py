import sys
import random
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),
'../../')))
from shared.student import STUDENT_NAME, GROUP_NAME, VARIANT_NUMBER

PASSWORDS = ["NetworkS3c!", "easy", "Firewa11@Pass", "anonymous",
"Intrus10n#Detect", "sample", "Malwar3@Scan", "qwerty", "Vulnerab1l!ty",
"common"]

CRITERIA = {"min_length": 9, "require_digits": True, "require_upper": True,
"require_special": True}

FORBIDDEN_PASSWORDS = {"easy", "anonymous", "sample", "qwerty", "common",
"password"}

SPECIAL_CHARS = set("!@#$%^&*()-_=+[]{}|;:,.<>?/")

def evaluate_password(password: str, full_list: list[str]) -> str:
    min_len = CRITERIA["min_length"]

    if password in FORBIDDEN_PASSWORDS or len(password) < min_len:
        return "Заборонений"

    has_digit = any(c.isdigit() for c in password)
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_special = any(c in SPECIAL_CHARS for c in password)

    all_criteria_met = has_digit and has_upper and has_lower and has_special

    if all_criteria_met:
        is_unique = full_list.count(password) == 1
        if len(password) >= min_len + 4 and is_unique:
            return "Дуже сильний"
        return "Сильний"

    if any([has_digit, has_upper, has_lower, has_special]):
        if len(password) >= min_len:
            return "Середній"
        return "Слабкий"

    return "Слабкий"

def run_task1() -> None:
    print("=" * 60)
    print(f"Завдання 1 | Студент: {STUDENT_NAME} | Варіант: {VARIANT_NUMBER}")
    print("=" * 60)

    work_passwords = list(PASSWORDS)

    random.seed(42)
    for _ in range(3):
        idx = random.randint(0, len(PASSWORDS) - 1)
        work_passwords.append(PASSWORDS[idx])

    print(f"{'№':<4} | {'Пароль':<20} | {'Статус':<15}")
    print("-" * 45)
    for i, pwd in enumerate(work_passwords, start=1):
        status = evaluate_password(pwd, work_passwords)
        print(f"{i:<4} | {pwd:<20} | {status:<15}")

if __name__ == "__main__":
    run_task1()