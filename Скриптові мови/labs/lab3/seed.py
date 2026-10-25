import json
import logging
import sqlite3
from contextlib import closing
from pathlib import Path

from labs.lab3.database import DATABASE_PATH, initialize_database

SEED_FILE = Path(__file__).resolve().parent / "data" / "seed.json"
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


def seed_database() -> None:
  initialize_database()

  if not SEED_FILE.exists():
    logging.error(f"Файл початкових даних {SEED_FILE} не знайдено.")
    return

  with SEED_FILE.open("r", encoding="utf-8-sig") as f:
    data = json.load(f)

  connection = sqlite3.connect(DATABASE_PATH)
  connection.execute("PRAGMA foreign_keys = ON")

  with closing(connection) as conn:
    cat_count = conn.execute("SELECT COUNT(*) FROM categories").fetchone()[0]
    rec_count = conn.execute("SELECT COUNT(*) FROM records").fetchone()[0]
    if cat_count > 0 or rec_count > 0:
      logging.info(
          "База даних уже містить записи. Початкове заповнення пропущено."
      )
      return

    try:
      with conn:
        for cat in data["categories"]:
          conn.execute(
              "INSERT INTO categories (id, name) VALUES (?, ?)",
              (cat["id"], cat["name"]),
          )

        for rec in data["records"]:
          conn.execute(
              """
                        INSERT INTO records (code, title, category_id, value, status)
                        VALUES (?, ?, ?, ?, ?)
                    """,
              (
                  rec["code"],
                  rec["title"],
                  rec["category_id"],
                  rec["value"],
                  rec["status"],
              ),
          )
      logging.info(
          "Успішно завантажено %d категорій та %d записів.",
          len(data["categories"]),
          len(data["records"]),
      )
    except sqlite3.Error as e:
      logging.error(f"Помилка заповнення бази (транзакцію скасовано): {e}")


if __name__ == "__main__":
  seed_database()