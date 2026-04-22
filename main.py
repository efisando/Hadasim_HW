from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.responses import FileResponse
import sqlite3

app = FastAPI(title="School Trip API")

# פונקציית עזר להתחברות לדיבי
def get_db():
    conn = sqlite3.connect('school_trip.db')
    conn.row_factory = sqlite3.Row # כדי שנוכל לגשת לעמודות לפי שם
    return conn

# יצירת טבלאות אם לא קיימות כבר (ירוץ פעם אחת בהתחלה)
def setup_database():
    conn = get_db()
    cursor = conn.cursor()
    
    # טבלת מורות
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Teachers (
            ID INTEGER PRIMARY KEY,
            FirstName TEXT NOT NULL,
            LastName TEXT NOT NULL,
            Class TEXT NOT NULL
        )
    ''')
    
    # טבלת תלמידות
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Students (
            ID INTEGER PRIMARY KEY,
            FirstName TEXT NOT NULL,
            LastName TEXT NOT NULL,
            Class TEXT NOT NULL
        )
    ''')
    
    # טבלת מיקומים
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Locations (
            StudentID INTEGER PRIMARY KEY,
            Latitude REAL,
            Longitude REAL,
            Timestamp TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

setup_database()


# --- מחלקות שמייצגות את הנתונים שמקבלים מהקליינט ---

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


# --- פונקציות עזר ---

# פונקציית המרה ממעלות (DMS) לעשרוני (DD)
def dms_to_dd(coord: CoordinatePart):
    degrees = float(coord.Degrees)
    minutes = float(coord.Minutes)
    seconds = float(coord.Seconds)
    return degrees + (minutes / 60) + (seconds / 3600)


# --- ראוטים של המערכת ---

# הוספת מורה חדשה
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
        print(f"Error: Teacher ID {teacher.ID} already exists in DB")
        return {"status": "error", "msg": "ID already exists"}
    finally:
        conn.close()

# הוספת תלמידה חדשה
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
        print(f"Error: Student ID {student.ID} already exists in DB")
        return {"status": "error", "msg": "ID already exists"}
    finally:
        conn.close()

# קבלת מיקום מהמכשיר
@app.post("/api/locations")
def update_location(data: LocationData):
    # המרת הקואורדינטות של התלמידה
    lat_decimal = dms_to_dd(data.Coordinates.Latitude)
    lon_decimal = dms_to_dd(data.Coordinates.Longitude)
    
    conn = get_db()
    cursor = conn.cursor()
    # שימוש ב-REPLACE כדי שאם התלמידה כבר קיימת בטבלת המיקומים, זה פשוט יעדכן לה את המיקום החדש
    cursor.execute(
        "REPLACE INTO Locations (StudentID, Latitude, Longitude, Timestamp) VALUES (?, ?, ?, ?)",
        (data.ID, lat_decimal, lon_decimal, data.Time)
    )
    conn.commit()
    conn.close()
    
    return {"status": "success", "msg": "Location updated on map!"}

# קבלת כל המורות
@app.get("/api/teachers")
def get_all_teachers():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Teachers")
    res = cursor.fetchall()
    conn.close()
    
    # ממירים את התוצאה לרשימה של מילונים
    return [dict(row) for row in res]

# קבלת תלמידות (אפשר לפי כיתה ואפשר את כולן)
@app.get("/api/students")
def get_all_students(class_name: str = None):
    conn = get_db()
    cursor = conn.cursor()
    
    # אם העבירו כיתה נסנן, אחרת נביא הכל
    if class_name != None:
        cursor.execute("SELECT * FROM Students WHERE Class = ?", (class_name,))
    else:
        cursor.execute("SELECT * FROM Students")
        
    res = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in res]

# שליפת כל המיקומים המעודכנים של התלמידות (עבור המפה)
@app.get("/api/locations")
def get_all_locations():
    conn = get_db()
    cursor = conn.cursor()
    # אנחנו עושים JOIN כדי לקבל לא רק את ה-ID, אלא גם את השם של התלמידה שיוצג על המפה!
    cursor.execute("""
        SELECT Locations.*, Students.FirstName, Students.LastName
        FROM Locations
        JOIN Students ON Locations.StudentID = Students.ID
    """)
    res = cursor.fetchall()
    conn.close()
    return [dict(row) for row in res]

# ראוט שמציג את דף המפה למורה בדפדפן
@app.get("/map")
def show_map():
    return FileResponse("map.html")