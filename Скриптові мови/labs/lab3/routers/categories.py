import sqlite3

from fastapi import APIRouter, HTTPException, status

from labs.lab3 import repository
from labs.lab3.schemas import CategoryCreate, CategoryRead

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.get("", response_model=list[CategoryRead], summary="Отримати список категорій")
def read_categories():
  return repository.get_all_categories()


@router.post(
    "",
    response_model=CategoryRead,
    status_code=status.HTTP_201_CREATED,
    summary="Створити категорію",
)
def create_category(category: CategoryCreate):
  try:
    return repository.create_category(category)
  except sqlite3.IntegrityError:
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=f"Категорія з назвою '{category.name}' вже існує",
    )


@router.delete(
    "/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Видалити порожню категорію",
)
def delete_category(category_id: int):
  if category_id <= 0:
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail="ID має бути > 0",
    )

  res = repository.delete_category(category_id)
  if res == "not_found":
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Категорію не знайдено"
    )
  if res == "has_records":
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="Неможливо видалити категорію, яка містить записи",
    )
