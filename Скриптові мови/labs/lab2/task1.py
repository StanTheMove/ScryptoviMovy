import hashlib
import hmac
import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone

PBKDF2_ITERATIONS = 100_000
SESSION_TIMEOUT_SEC = 900


class User:
    def __init__(self, username: str, email: str, role: str = "user"):
        self.username = username
        self.role = role
        self.active = True
        self._email = ""
        self.email = email

        self.__password_salt: bytes = b""
        self.__password_hash: bytes = b""

    @property
    def email(self) -> str:
        return self._email

    @email.setter
    def email(self, value: str) -> None:
        pattern = r"^[a-zA-Z][a-zA-Z0-9_.]{2,63}@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        if not re.match(pattern, value):
            raise ValueError(f"Некоректний формат email-адреси: {value}")
        self._email = value

    def set_password(self, password: str) -> None:
        self.__password_salt = os.urandom(16)
        self.__password_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            self.__password_salt,
            PBKDF2_ITERATIONS,
        )

    def check_password(self, password: str) -> bool:
        if not self.__password_hash or not self.__password_salt:
            return False
        calculated_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            self.__password_salt,
            PBKDF2_ITERATIONS,
        )
        return hmac.compare_digest(self.__password_hash, calculated_hash)

    def deactivate(self) -> None:
        self.active = False

    def __str__(self) -> str:
        status = "Active" if self.active else "Inactive"
        return f"User(username='{self.username}', email='{self.email}', role='{self.role}', status='{status}')"


class Admin(User):
    def __init__(
        self,
        username: str,
        email: str,
        permissions: list[str] | set[str] | None = None,
    ):
        super().__init__(username, email, role="admin")
        self.permissions: set[str] = set(permissions) if permissions else set()

    def grant_permission(self, permission: str) -> None:
        self.permissions.add(permission)

    def revoke_permission(self, permission: str) -> None:
        self.permissions.discard(permission)

    def has_permission(self, permission: str) -> bool:
        return permission in self.permissions

    def __str__(self) -> str:
        perms_str = ", ".join(sorted(self.permissions)) if self.permissions else "None"
        return f"Admin(username='{self.username}', email='{self.email}', permissions=[{perms_str}])"


class Session:
    def __init__(self, ip: str):
        self.ip = ip
        self.login_time = datetime.now(timezone.utc)
        self.last_activity = self.login_time

    def touch(self) -> None:
        self.last_activity = datetime.now(timezone.utc)

    def is_active(self, timeout_sec: int) -> bool:
        if timeout_sec <= 0:
            raise ValueError("Таймаут повинен бути строго додатнім числом!")
        delta = datetime.now(timezone.utc) - self.last_activity
        return delta.total_seconds() < timeout_sec


@dataclass(frozen=True)
class AuditEntry:
    timestamp: datetime
    username: str
    action: str


class AuditLog:
    def __init__(self):
        self._logs: list[AuditEntry] = []

    def add_log(self, username: str, action: str) -> None:
        entry = AuditEntry(
            timestamp=datetime.now(timezone.utc), username=username, action=action
        )
        self._logs.append(entry)

    def show_all(self) -> list[AuditEntry]:
        return self._logs


class UserAccount:
    def __init__(self, user: User):
        self.user = user
        self.audit_log = AuditLog()
        self.session: Session | None = None

    def login(self, username: str, password: str, ip: str) -> bool:
        if not self.user.active or self.user.username != username:
            self.audit_log.add_log(username, "login_failure")
            return False

        if self.user.check_password(password):
            self.session = Session(ip)
            self.session.touch()
            self.audit_log.add_log(username, "login_success")
            return True

        self.audit_log.add_log(username, "login_failure")
        return False

    def is_authenticated(self) -> bool:
        return self.session is not None and self.session.is_active(SESSION_TIMEOUT_SEC)

    def logout(self) -> None:
        if self.session:
            self.session = None
            self.audit_log.add_log(self.user.username, "logout")

    def __getitem__(self, key: str):
        if key in ("__password_hash", "__password_salt", "password"):
            raise KeyError("Прямий доступ до хешу та солі пароля суворо заборонено!")
        if hasattr(self, key):
            return getattr(self, key)
        raise KeyError(f"Невідомий атрибут: {key}")

    def __setitem__(self, key: str, value) -> None:
        if key == "user":
            if not isinstance(value, User):
                raise TypeError("Поле 'user' повинно бути екземпляром класу User!")
            self.user = value
        elif key == "session":
            if value is not None and not isinstance(value, Session):
                raise TypeError(
                    "Поле 'session' повинно бути екземпляром Session або None!"
                )
            self.session = value
        else:
            raise KeyError(f"Зміна поля '{key}' заборонена або поле не існує")


def run_demo() -> None:

    print("\n1. Створення користувача та валідація email:")
    user = User("stask", "stask.dev@example.com")
    user.set_password("SuperSecretPass123!")
    print(f"Створено: {user}")

    try:
        print("Спроба встановити некоректний email 'bad-email':")
        user.email = "bad-email"
    except ValueError as e:
        print(f"Очікуване перехоплення помилки: {e}")

    print("\n2. Робота з класом Admin (наслідування та права):")
    admin = Admin("root_admin", "admin.corp@example.com", ["read", "write"])
    admin.grant_permission("delete")
    print(f"Адміністратор: {admin}")
    print(f"Чи є право 'delete': {admin.has_permission('delete')}")
    admin.revoke_permission("write")
    print(f"Після відкликання 'write': {admin}")

    print("\n3. Тестування UserAccount, автентифікації та сесій:")
    account = UserAccount(user)

    print("Спроба входу з невірним паролем:")
    assert not account.login("stask", "WrongPassword", "192.168.1.15")
    print("Результат: Вхід відхилено.")

    print("Спроба входу з правильним паролем:")
    assert account.login("stask", "SuperSecretPass123!", "192.168.1.15")
    print(f"Результат: Успішно! is_authenticated = {account.is_authenticated()}")

    print("\n4. Перевірка таймауту сесії (імітація 0 секунд):")
    print(f"Активність за таймаутом 0 сек: {account.session.is_active(1)}")

    print("\n5. Тестування магічних методів __getitem__ / __setitem__:")
    print(f"Доступ через account['user']: {account['user'].username}")
    try:
        _ = account["__password_hash"]
    except KeyError as e:
        print(f"Очікуване блокування доступу до секретів: {e}")

    print("\n6. Завершення сеансу та вивід AuditLog:")
    account.logout()
    print(f"Стан після logout: is_authenticated = {account.is_authenticated()}")

    print("\nЗаписи журналу аудиту:")
    for entry in account.audit_log.show_all():
        print(
            f"[{entry.timestamp.isoformat()}] User: {entry.username:10} | Action: {entry.action}"
        )
