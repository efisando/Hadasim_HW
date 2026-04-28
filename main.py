from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.responses import FileResponse
import sqlite3
import math

app = FastAPI(title="School Trip API")


def get_db():
    # Open connection to the local SQLite database
    conn = sqlite3.connect("school_trip.db")
    conn.row_factory = sqlite3.Row
    return conn


def setup_database():
    # Create the required tables if they do not already exist
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Teachers (
            ID INTEGER PRIMARY KEY,
            FirstName TEXT NOT NULL,
            LastName TEXT NOT NULL,
            Class TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Students (
            ID INTEGER PRIMARY KEY,
            FirstName TEXT NOT NULL,
            LastName TEXT NOT NULL,
            Class TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Locations (
            StudentID INTEGER PRIMARY KEY,
            Latitude REAL,
            Longitude REAL,
            Timestamp TEXT
        )
    """)

    conn.commit()
    conn.close()


setup_database()


# Request models

class Teacher(BaseModel):
    ID: int
    FirstName: str
    LastName: str
    Class: str


class Student(BaseModel):
    ID: int
    FirstName: str
    LastName: str
    Class: str


class CoordinatePart(BaseModel):
    Degrees: str
    Minutes: str
    Seconds: str


class Coordinates(BaseModel):
    Longitude: CoordinatePart
    Latitude: CoordinatePart


class LocationData(BaseModel):
    ID: int
    Coordinates: Coordinates
    Time: str


def dms_to_dd(coord: CoordinatePart):
    # Convert GPS coordinates from DMS format to decimal degrees
    degrees = float(coord.Degrees)
    minutes = float(coord.Minutes)
    seconds = float(coord.Seconds)
    return degrees + (minutes / 60) + (seconds / 3600)


@app.post("/api/teachers")
def add_new_teacher(teacher: Teacher):
    conn = get_db()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT INTO Teachers (ID, FirstName, LastName, Class) VALUES (?, ?, ?, ?)",
            (teacher.ID, teacher.FirstName, teacher.LastName, teacher.Class)
        )
        conn.commit()
        return {"status": "success", "msg": "Teacher added!"}

    except sqlite3.IntegrityError:
        return {"status": "error", "msg": "Teacher ID already exists"}

    finally:
        conn.close()


@app.post("/api/students")
def add_new_student(student: Student):
    conn = get_db()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT INTO Students (ID, FirstName, LastName, Class) VALUES (?, ?, ?, ?)",
            (student.ID, student.FirstName, student.LastName, student.Class)
        )
        conn.commit()
        return {"status": "success", "msg": "Student added!"}

    except sqlite3.IntegrityError:
        return {"status": "error", "msg": "Student ID already exists"}

    finally:
        conn.close()


@app.post("/api/locations")
def update_location(data: LocationData):
    lat_decimal = dms_to_dd(data.Coordinates.Latitude)
    lon_decimal = dms_to_dd(data.Coordinates.Longitude)

    conn = get_db()
    cursor = conn.cursor()

    # Keep only the latest location for each student
    cursor.execute(
        "REPLACE INTO Locations (StudentID, Latitude, Longitude, Timestamp) VALUES (?, ?, ?, ?)",
        (data.ID, lat_decimal, lon_decimal, data.Time)
    )

    conn.commit()
    conn.close()

    return {"status": "success", "msg": "Location updated!"}


@app.get("/api/teachers")
def get_all_teachers():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM Teachers")
    res = cursor.fetchall()

    conn.close()
    return [dict(row) for row in res]


@app.get("/api/teachers/{teacher_id}")
def get_teacher(teacher_id: int):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM Teachers WHERE ID = ?", (teacher_id,))
    res = cursor.fetchone()

    conn.close()

    if res:
        return dict(res)

    return {"status": "error", "msg": "Teacher not found"}


@app.get("/api/students")
def get_all_students(class_name: str = None):
    conn = get_db()
    cursor = conn.cursor()

    # Optional filter: return only students from a specific class
    if class_name is not None:
        cursor.execute("SELECT * FROM Students WHERE Class = ?", (class_name,))
    else:
        cursor.execute("SELECT * FROM Students")

    res = cursor.fetchall()
    conn.close()

    return [dict(row) for row in res]


@app.get("/api/students/{student_id}")
def get_student(student_id: int):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM Students WHERE ID = ?", (student_id,))
    res = cursor.fetchone()

    conn.close()

    if res:
        return dict(res)

    return {"status": "error", "msg": "Student not found"}


@app.get("/api/teachers/{teacher_id}/students")
def get_students_by_teacher(teacher_id: int):
    conn = get_db()
    cursor = conn.cursor()

    # First get the teacher's class, then return students from the same class
    cursor.execute("SELECT Class FROM Teachers WHERE ID = ?", (teacher_id,))
    teacher = cursor.fetchone()

    if not teacher:
        conn.close()
        return {"status": "error", "msg": "Teacher not found"}

    cursor.execute("SELECT * FROM Students WHERE Class = ?", (teacher["Class"],))
    students = cursor.fetchall()

    conn.close()

    return [dict(row) for row in students]


@app.get("/api/locations")
def get_all_locations():
    conn = get_db()
    cursor = conn.cursor()

    # Join with Students table so the map can show names, not only IDs
    cursor.execute("""
        SELECT Locations.*, Students.FirstName, Students.LastName
        FROM Locations
        JOIN Students ON Locations.StudentID = Students.ID
    """)

    res = cursor.fetchall()
    conn.close()

    return [dict(row) for row in res]


@app.get("/map")
def show_map():
    return FileResponse("map.html")


# Bonus feature - distance alerts

def calculate_distance_km(lat1, lon1, lat2, lon2):
    # Haversine formula for distance between two GPS points
    radius = 6371.0

    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1_rad)
        * math.cos(lat2_rad)
        * math.sin(dlon / 2) ** 2
    )

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return radius * c


@app.post("/api/alerts")
def check_distance(teacher_data: LocationData):
    teacher_lat = dms_to_dd(teacher_data.Coordinates.Latitude)
    teacher_lon = dms_to_dd(teacher_data.Coordinates.Longitude)

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT Locations.*, Students.FirstName, Students.LastName
        FROM Locations
        JOIN Students ON Locations.StudentID = Students.ID
    """)

    students = cursor.fetchall()
    conn.close()

    alerts = []

    for student in students:
        distance = calculate_distance_km(
            teacher_lat,
            teacher_lon,
            student["Latitude"],
            student["Longitude"]
        )

        # Alert only if the student is more than 3 km away
        if distance > 3.0:
            alerts.append({
                "Name": f"{student['FirstName']} {student['LastName']}",
                "DistanceKM": round(distance, 2)
            })

    return {"status": "success", "alerts": alerts}