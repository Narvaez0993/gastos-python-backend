from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel

class PersonCreate(BaseModel):
    name: str

class PersonUpdate(BaseModel):
    name: str

class PersonOut(BaseModel):
    id: int
    name: str
    created_at: str
