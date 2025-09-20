"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from sqlalchemy import create_engine, MetaData, Table, Column, String, Integer
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
import os
from pathlib import Path
from typing import Generator

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

# Database setup
database_url = "postgresql://postgres:postgres@localhost:5432/mergington"
engine = create_engine(database_url)
metadata = MetaData()

# Define activities table
activities_table = Table(
    "activities",
    metadata,
    Column("name", String, primary_key=True),
    Column("description", String),
    Column("schedule", String),
    Column("max_participants", Integer),
    Column("participants", String),  # Comma-separated emails
)

metadata.create_all(engine)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Simplify type annotations to avoid compatibility issues
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities(db = Depends(get_db)):
    result = db.execute(activities_table.select()).fetchall()
    return [dict(row) for row in result]


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: str, db = Depends(get_db)):
    activity = db.execute(activities_table.select().where(activities_table.c.name == activity_name)).fetchone()
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    participants = activity.participants.split(",") if activity.participants else []
    if email in participants:
        raise HTTPException(status_code=400, detail="Student is already signed up")

    participants.append(email)
    db.execute(
        activities_table.update()
        .where(activities_table.c.name == activity_name)
        .values(participants=",".join(participants))
    )
    db.commit()
    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(activity_name: str, email: str, db = Depends(get_db)):
    activity = db.execute(activities_table.select().where(activities_table.c.name == activity_name)).fetchone()
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    participants = activity.participants.split(",") if activity.participants else []
    if email not in participants:
        raise HTTPException(status_code=400, detail="Student is not signed up for this activity")

    participants.remove(email)
    db.execute(
        activities_table.update()
        .where(activities_table.c.name == activity_name)
        .values(participants=",".join(participants))
    )
    db.commit()
    return {"message": f"Unregistered {email} from {activity_name}"}
