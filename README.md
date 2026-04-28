# 📍 School Trip Tracker - Real-Time Location API

A full-stack tracking system designed to monitor and manage student locations in real-time during school trips.  
The system enables teachers to visualize student positions on an interactive map and receive alerts for distance violations.

---

## 🛠 Tech Stack & Dependencies

- **Backend:** Python + FastAPI  
- **Database:** SQLite  
- **Frontend:** HTML / JavaScript + Leaflet.js  
- **Server:** Uvicorn  

### Prerequisites

- Python 3.10+
- Modern web browser

---

## 🚀 Installation & Setup

### 1. Create and activate virtual environment

    python -m venv venv
    venv\Scripts\activate

### 2. Install dependencies

    pip install fastapi uvicorn pydantic

### 3. Run the server

    uvicorn main:app --reload

Server will be available at:  
http://localhost:8000

---

## 💻 Usage Guide

### API Interface
**http://localhost:8000/docs**
Used for inserting and retrieving teachers, students, and locations.

### Teacher Map Dashboard
**http://localhost:8000/map**
Interactive map that displays student locations and updates automatically.

---

## 💡 Simplifying Assumptions (הנחות מקלות)

During the development of this project, the following simplifying assumptions were made, as required:
1. **Location Updates (Polling vs. WebSockets):** Instead of implementing a complex bidirectional WebSocket connection for real-time data push, the system relies on the client-side map polling the server every 10 seconds.
2. **Local Database:** SQLite was chosen for local data storage (`school_trip.db`). It is assumed that for the scope of this educational assignment, deploying a remote database is unnecessary.
3. **Authentication & Authorization:** The system assumes the map and Swagger UI represent the teacher's secure interfaces. Therefore, a full user login/authentication mechanism was omitted.
4. **ID Format:** Israeli ID numbers (9 digits) are stored as standard Integers in the database for query convenience.

---

## 🚨 Bonus Feature – Distance Alerts

The system includes a bonus feature that calculates the distance between the teacher and all students using the Haversine formula.
Alerts are triggered when a student is more than 3 km away.

---

## 📡 Example API Requests

### Add Student
`POST /api/students`

    {
      "ID": 1,
      "FirstName": "Noa",
      "LastName": "Levi",
      "Class": "A1"
    }

### Update Location
`POST /api/locations`

    {
      "ID": 1,
      "Coordinates": {
        "Latitude": {
          "Degrees": "32",
          "Minutes": "5",
          "Seconds": "30"
        },
        "Longitude": {
          "Degrees": "34",
          "Minutes": "48",
          "Seconds": "15"
        }
      },
      "Time": "2026-04-29T12:00:00"
    }

---

## 🗄 Database Design

The system uses a SQLite database with three tables:
- Teachers
- Students
- Locations

Each student has only one active location.  
The location is updated using `REPLACE` in order to store the latest known position.

---

## 📌 API Design Notes

The API follows the assignment requirements:

- Data insertion is handled using `POST` requests  
- Data retrieval is handled using `GET` requests  
- Update and delete operations (`PUT`, `PATCH`, `DELETE`) were intentionally not implemented  

The `/api/alerts` endpoint is an optional bonus feature.

---

## 📂 Project Structure

    main.py          # Backend application, database logic and API routes
    map.html         # Frontend map dashboard
    school_trip.db   # SQLite database file

---

## 📸 Screenshots

### Live Map View
![Map View](./screenshots/map_view.png)

### Distance Alert
![Distance Alert](./screenshots/distance_alert.png)

### Swagger UI
![Swagger UI](./screenshots/swagger_ui.png)
![Swagger UI](./screenshots/swagger_ui2.png)
---

## 🎯 Summary

This project demonstrates:
- Full-stack development
- RESTful API design with FastAPI
- SQLite database usage
- Real-time location tracking
- Geospatial distance calculations
- Interactive map visualization
