from contextlib import closing

from labs.lab3.database import get_connection
from labs.lab3.schemas import CategoryCreate, RecordCreate, RecordReplace


def get_all_categories() -> list[dict]:
  with closing(get_connection()) as conn:
    rows = conn.execute(
        "SELECT id, name FROM categories ORDER BY id ASC"
    ).fetchall()
    return [dict(r) for r in rows]


def get_category_by_id(category_id: int) -> dict | None:
  with closing(get_connection()) as conn:
    row = conn.execute(
        "SELECT id, name FROM categories WHERE id = ?", (category_id,)
    ).fetchone()
    return dict(row) if row else None


def create_category(category: CategoryCreate) -> dict:
  with closing(get_connection()) as conn:
    with conn:
      cursor = conn.execute(
          "INSERT INTO categories (name) VALUES (?)", (category.name,)
      )
      new_id = cursor.lastrowid
    return {"id": new_id, "name": category.name}


def delete_category(category_id: int) -> str:

  with closing(get_connection()) as conn:
    cat = conn.execute(
        "SELECT id FROM categories WHERE id = ?", (category_id,)
    ).fetchone()
    if not cat:
      return "not_found"

    records_count = conn.execute(
        "SELECT COUNT(*) as cnt FROM records WHERE category_id = ?",
        (category_id,),
    ).fetchone()["cnt"]
    if records_count > 0:
      return "has_records"

    with conn:
      conn.execute("DELETE FROM categories WHERE id = ?", (category_id,))
    return "ok"


_SELECT_JOIN_QUERY = """
    SELECT r.id, r.code, r.title, r.category_id, c.name AS category_name, r.value, r.status
    FROM records r
    JOIN categories c ON r.category_id = c.id
"""


def get_records(
    category_id: int | None = None,
    status: str | None = None,
    min_value: float | None = None,
    q: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> list[dict]:
  query = _SELECT_JOIN_QUERY
  conditions = []
  params: list = []

  if category_id is not None:
    conditions.append("r.category_id = ?")
    params.append(category_id)
  if status is not None:
    conditions.append("r.status = ?")
    params.append(status)
  if min_value is not None:
    conditions.append("r.value >= ?")
    params.append(min_value)
  if q is not None:
    conditions.append("instr(r.title, ?) > 0")
    params.append(q)

  if conditions:
    query += " WHERE " + " AND ".join(conditions)

  query += " ORDER BY r.id ASC LIMIT ? OFFSET ?"
  params.extend([limit, offset])

  with closing(get_connection()) as conn:
    rows = conn.execute(query, params).fetchall()
    return [dict(r) for r in rows]


def get_record_by_id(record_id: int) -> dict | None:
  query = _SELECT_JOIN_QUERY + " WHERE r.id = ?"
  with closing(get_connection()) as conn:
    row = conn.execute(query, (record_id,)).fetchone()
    return dict(row) if row else None


def create_record(record: RecordCreate) -> dict:
  with closing(get_connection()) as conn, conn:
    cursor = conn.execute(
        """
                INSERT INTO records (code, title, category_id, value, status)
                VALUES (?, ?, ?, ?, ?)
            """,
        (
            record.code,
            record.title,
            record.category_id,
            record.value,
            record.status,
        ),
    )
    new_id = cursor.lastrowid
  return get_record_by_id(new_id)  # type: ignore


def replace_record(record_id: int, record: RecordReplace) -> dict | None:
  with closing(get_connection()) as conn:
    existing = conn.execute(
        "SELECT id FROM records WHERE id = ?", (record_id,)
    ).fetchone()
    if not existing:
      return None

    with conn:
      conn.execute(
          """
                UPDATE records
                SET code = ?, title = ?, category_id = ?, value = ?, status = ?
                WHERE id = ?
            """,
          (
              record.code,
              record.title,
              record.category_id,
              record.value,
              record.status,
              record_id,
          ),
      )
  return get_record_by_id(record_id)


def delete_record(record_id: int) -> bool:
  with closing(get_connection()) as conn:
    existing = conn.execute(
        "SELECT id FROM records WHERE id = ?", (record_id,)
    ).fetchone()
    if not existing:
      return False
    with conn:
      conn.execute("DELETE FROM records WHERE id = ?", (record_id,))
    return True


def create_records_bulk(records: list[RecordCreate]) -> list[dict]:
  with closing(get_connection()) as conn:
    codes = [r.code for r in records]
    if len(codes) != len(set(codes)):
      raise ValueError("duplicate_in_payload")

    cat_ids = {r.category_id for r in records}
    placeholders = ",".join("?" * len(cat_ids))
    found_cats = conn.execute(
        f"SELECT id FROM categories WHERE id IN ({placeholders})", list(cat_ids)
    ).fetchall()
    if len(found_cats) != len(cat_ids):
      raise LookupError("category_not_found")

    code_placeholders = ",".join("?" * len(codes))
    existing_codes = conn.execute(
        f"SELECT code FROM records WHERE code IN ({code_placeholders})", codes
    ).fetchall()
    if existing_codes:
      raise ValueError("code_conflict")

    created_ids = []
    with conn:
      for r in records:
        cursor = conn.execute(
            """
                    INSERT INTO records (code, title, category_id, value, status)
                    VALUES (?, ?, ?, ?, ?)
                """,
            (r.code, r.title, r.category_id, r.value, r.status),
        )
        created_ids.append(cursor.lastrowid)

  return [get_record_by_id(rid) for rid in created_ids]  # type: ignore