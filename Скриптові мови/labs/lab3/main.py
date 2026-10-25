from contextlib import asynccontextmanager

from fastapi import FastAPI

from labs.lab3 import config
from labs.lab3.database import initialize_database
from labs.lab3.routers import categories, records
from labs.lab3.schemas import StudentRead
from shared import student


@asynccontextmanager
async def lifespan(app: FastAPI):
  initialize_database()
  yield


app = FastAPI(
    title=config.APP_TITLE,
    description=config.APP_DESCRIPTION,
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(categories.router)
app.include_router(records.router)


@app.get("/ping", tags=["Service"], summary="Перевірка доступності сервісу")
def ping():
  return {"status": "ok"}


@app.get(
    "/student",
    response_model=StudentRead,
    tags=["Service"],
    summary="Дані студента",
)
def get_student_info():
  return {
      "student_name": getattr(student, "STUDENT_NAME", "Холопкін Станіслав"),
      "group_name": getattr(student, "GROUP_NAME", "КБ-204"),
      "variant_number": config.VARIANT_NUMBER,
  }