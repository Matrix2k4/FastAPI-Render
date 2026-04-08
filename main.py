from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base, Session

app = FastAPI()

# SQLite Database URL
DATABASE_URL = "sqlite:///./students.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# SQLAlchemy Model (Table)
class StudentDB(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    age = Column(Integer)
    city = Column(String)
    country = Column(String)

# Create table
Base.metadata.create_all(bind=engine)


# Pydantic Models
class Address(BaseModel):
    city: str
    country: str


class Student(BaseModel):
    name: str
    age: int
    address: Address


# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# CREATE
@app.post("/students", status_code=201)
async def create_student(student: Student):
    db = next(get_db())

    new_student = StudentDB(
        name=student.name,
        age=student.age,
        city=student.address.city,
        country=student.address.country
    )

    db.add(new_student)
    db.commit()
    db.refresh(new_student)

    return {"id": new_student.id}


# READ ALL
@app.get("/students", response_model=list[Student])
async def list_students(country: str = None, age: int = None):
    db = next(get_db())

    query = db.query(StudentDB)

    if country:
        query = query.filter(StudentDB.country == country)
    if age:
        query = query.filter(StudentDB.age >= age)

    students = query.all()

    return [
        {
            "name": s.name,
            "age": s.age,
            "address": {"city": s.city, "country": s.country}
        }
        for s in students
    ]


# READ ONE
@app.get("/students/{id}", response_model=Student)
async def get_student(id: int):
    db = next(get_db())

    student = db.query(StudentDB).filter(StudentDB.id == id).first()

    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    return {
        "name": student.name,
        "age": student.age,
        "address": {"city": student.city, "country": student.country}
    }


# UPDATE
@app.patch("/students/{id}", status_code=204)
async def update_student(id: int, student: Student):
    db = next(get_db())

    db_student = db.query(StudentDB).filter(StudentDB.id == id).first()

    if not db_student:
        raise HTTPException(status_code=404, detail="Student not found")

    db_student.name = student.name
    db_student.age = student.age
    db_student.city = student.address.city
    db_student.country = student.address.country

    db.commit()


# DELETE
@app.delete("/students/{id}", status_code=200)
async def delete_student(id: int):
    db = next(get_db())

    student = db.query(StudentDB).filter(StudentDB.id == id).first()

    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    db.delete(student)
    db.commit()

    return {"message": "Student deleted successfully"}
