# Module Templates

Purpose

Define reusable templates for automatically generating code modules.

---

# API Router Template

File

api/routers/example_router.py

Template

from fastapi import APIRouter, Depends
from api.services.example_service import ExampleService

router = APIRouter()

@router.get("/example")
async def get_example(service: ExampleService = Depends()):
    return service.get_example()

---

# Service Template

File

api/services/example_service.py

Template

class ExampleService:

    def __init__(self, repository):
        self.repository = repository

    def get_example(self):
        return self.repository.get_all()

---

# Repository Template

File

api/repositories/example_repository.py

Template

class ExampleRepository:

    def __init__(self, session):
        self.session = session

    def get_all(self):
        return self.session.query(...).all()

---

# Database Model Template

File

api/models/example_model.py

Template

from sqlalchemy import Column, Integer, String
from api.database.base import Base

class Example(Base):

    __tablename__ = "example"

    id = Column(Integer, primary_key=True)
    name = Column(String)

---

# Pydantic Schema Template

File

api/schemas/example_schema.py

Template

from pydantic import BaseModel

class ExampleSchema(BaseModel):

    name: str

---

# Worker Template

File

workers/example_worker.py

Template

def run_task(payload):

    process(payload)

    return True

---

# Bot Handler Template

File

bot/handlers/example_handler.py

Template

from aiogram import Router

router = Router()

@router.message()
async def handle_message(message):
    await message.answer("Example response")

---

# Test Template

File

tests/test_example.py

Template

def test_example():

    assert True