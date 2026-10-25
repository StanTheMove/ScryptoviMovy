from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class CategoryCreate(BaseModel):

  model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
  name: str = Field(min_length=2, max_length=40)


class CategoryRead(BaseModel):

  model_config = ConfigDict(from_attributes=True)
  id: int
  name: str

class RecordCreate(BaseModel):

  model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
  code: str = Field(min_length=3, max_length=40)
  title: str = Field(min_length=3, max_length=120)
  category_id: int = Field(gt=0)
  value: float = Field(ge=0, allow_inf_nan=False)
  status: Literal["new", "in_progress", "done"]


class RecordReplace(RecordCreate):
  pass


class RecordRead(BaseModel):

  model_config = ConfigDict(from_attributes=True)
  id: int
  code: str
  title: str
  category_id: int
  category_name: str
  value: float
  status: Literal["new", "in_progress", "done"]

class StudentRead(BaseModel):

  student_name: str
  group_name: str
  variant_number: int