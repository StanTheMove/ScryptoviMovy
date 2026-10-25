"""Маршрути для роботи із записами вимірювань."""

import sqlite3

from fastapi import APIRouter, HTTPException, Query, status

from labs.lab3 import repository
from labs.lab3.schemas import RecordCreate, RecordRead, RecordReplace

router = APIRouter(prefix="/records", tags=["Records"])


@router.get("", response_model=list[RecordRead], summary="Отримати список записів з фільтрами")
def read_records(
    category_id: int | None = Query(None, gt=0),
    status_val: str | None = Query(None, alias="status"),
    min_value: float | None = Query(None, ge=0),
    q: str | None = Query(None, min_length=1, max_length=120),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
  if status_val and status_val not in ("new", "in_progress", "done"):
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail="Недозволений статус",
    )
  return repository.get_records(
      category_id=category_id,
      status=status_val,
      min_value=min_value,
      q=q,
      limit=limit,
      offset=offset,
  )


@router.get("/{record_id}", response_model=RecordRead, summary="Отримати один запис")
def read_record(record_id: int):
  if record_id <= 0:
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail="ID має бути > 0",
    )
  record = repository.get_record_by_id(record_id)
  if not record:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Запис не знайдено"
    )
  return record


@router.post(
    "",
    response_model=RecordRead,
    status_code=status.HTTP_201_CREATED,
    summary="Створити запис",
)
def create_record(record: RecordCreate):
  cat = repository.get_category_by_id(record.category_id)
  if not cat:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Категорію з ID {record.category_id} не знайдено",
    )

  try:
    return repository.create_record(record)
  except sqlite3.IntegrityError:
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=f"Запис із кодом '{record.code}' вже існує",
    )


@router.put("/{record_id}", response_model=RecordRead, summary="Повна заміна запису")
def replace_record(record_id: int, record: RecordReplace):
  if record_id <= 0:
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail="ID має бути > 0",
    )

  cat = repository.get_category_by_id(record.category_id)
  if not cat:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Категорію з ID {record.category_id} не знайдено",
    )

  try:
    updated = repository.replace_record(record_id, record)
    if not updated:
      raise HTTPException(
          status_code=status.HTTP_404_NOT_FOUND, detail="Запис не знайдено"
      )
    return updated
  except sqlite3.IntegrityError:
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=f"Запис із кодом '{record.code}' вже існує",
    )


@router.delete(
    "/{record_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Видалити запис",
)
def delete_record(record_id: int):
  if record_id <= 0:
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail="ID має бути > 0",
    )
  success = repository.delete_record(record_id)
  if not success:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Запис не знайдено"
    )


@router.post(
    "/bulk",
    response_model=list[RecordRead],
    status_code=status.HTTP_201_CREATED,
    summary="Пакетне додавання записів",
)
def create_records_bulk(records: list[RecordCreate]):
  if not (1 <= len(records) <= 100):
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail="Розмір пакета повинен бути від 1 до 100 елементів",
    )

  try:
    return repository.create_records_bulk(records)
  except LookupError:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Пакет містить посилання на неіснуючу категорію",
    )
  except ValueError as e:
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=(
            f"Конфлікт унікальності коду в пакеті або базі ({e})"
        ),
    )
  except sqlite3.IntegrityError as e:
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=f"Порушення обмежень цілісності бази: {e}",
    )