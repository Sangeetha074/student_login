import mysql.connector
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List

app = FastAPI()

# Configure CORS to allow frontend origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Adjust for your frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db_connection():
    connection = mysql.connector.connect(
        host="auth-db1834.hstgr.io",
        user="u651328475_fastapi",
        password="U651328475_fastapi",
        database="u651328475_fastapi",
        use_pure=True
    )
    return connection

# Basic Authentication setup
security = HTTPBasic()
VALID_USERNAME = "Ram"
VALID_PASSWORD = "1234"

def basic_auth(credentials: HTTPBasicCredentials = Depends(security)):
    if credentials.username != VALID_USERNAME or credentials.password != VALID_PASSWORD:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

@app.get("/")
def root():
    return {"message": "Welcome to the FastAPI app"}

@app.post("/data")
def get_secure_data(username: str = Depends(basic_auth)):
    return {
        "message": "Access granted",
        "username": username,
    }

class Item(BaseModel):
    username: str
    password: str

@app.post("/reg")
def login_user(obj: Item):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT username, password FROM userinform")
    users = cursor.fetchall()

    for db_username, db_password in users:
        if obj.username.strip() == db_username.strip() and obj.password.strip() == str(db_password).strip():
            cursor.close()
            conn.close()
            return {"status": "Success", "message": "Login successful"}

    cursor.close()
    conn.close()
    return {"status": "Failure", "message": "Invalid username or password"}

@app.post("/num")
def get_secure_data_num(username: str = Depends(basic_auth)):
    return {"message": "Access granted", "username": username}

@app.post("/insert")
def insert_data(user: Item):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        query = "INSERT INTO userinform (username, password) VALUES (%s, %s)"
        cursor.execute(query, (user.username, user.password))
        conn.commit()
        return {"message": "Data inserted successfully", "data": user.dict()}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to insert data: {str(e)}")
    finally:
        cursor.close()
        conn.close()

class ForgotPasswordRequest(BaseModel):
    username: str
    new_password: str

@app.post("/forgot_password")
def forgot_password(request: ForgotPasswordRequest):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT username FROM userinform WHERE username = %s", (request.username,))
    user = cursor.fetchone()

    if not user:
        cursor.close()
        conn.close()
        raise HTTPException(status_code=404, detail="User not found")

    cursor.execute("UPDATE userinform SET password = %s WHERE username = %s", (request.new_password, request.username))
    conn.commit()
    cursor.close()
    conn.close()

    return {"status": "Success", "message": "Password updated successfully"}

@app.get("/usersinform")
def get_users():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT username, password FROM userinform")
        users = cursor.fetchall()
        # Assuming userinform columns: username, password (adjust if needed)
        return [{"username": user[0], "password": user[1]} for user in users]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching users: {str(e)}")
    finally:
        cursor.close()
        conn.close()

class Student(BaseModel):
    Name: str
    email: str
    phone: str
    dob: str
    gender: str
    Department: str
    Semester: int
    CGPA: float

@app.post("/stform")
def register_student(student: Student):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM student WHERE email = %s OR phone = %s", (student.email, student.phone))
        existing_student = cursor.fetchone()

        if existing_student:
            raise HTTPException(status_code=400, detail="Email or phone already registered")

        query = """
        INSERT INTO student (Name, email, phone, dob, gender, Department, Semester, CGPA) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        values = (student.Name, student.email, student.phone, student.dob, student.gender,
                  student.Department, student.Semester, student.CGPA)
        cursor.execute(query, values)
        conn.commit()
        return {"message": "Student registered successfully"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to register student: {str(e)}")
    finally:
        cursor.close()
        conn.close()

class SearchQuery(BaseModel):
    Search: str

@app.post("/search")
def search_students(query: SearchQuery):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        search_term = f"%{query.Search}%"
        sql_query = """
        SELECT * FROM student
        WHERE Name LIKE %s OR email LIKE %s OR phone LIKE %s OR Department LIKE %s OR Semester LIKE %s OR CGPA LIKE %s
        """
        cursor.execute(sql_query, (search_term, search_term, search_term, search_term, search_term, search_term))
        results = cursor.fetchall()
        return [
            {
                "sid": stu[0],
                "Name": stu[1],
                "Department": stu[2],
                "Semester": stu[3],
                "CGPA": stu[4],
                "email": stu[5],
                "phone": stu[6],
                "gender": stu[7],
                "dob": stu[8]
            }
            for stu in results
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

class DepartmentItem(BaseModel):
    Department: str

@app.post("/dep")
def filter_students_by_department(obj: DepartmentItem):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        query = "SELECT * FROM student WHERE Department = %s"
        cursor.execute(query, (obj.Department,))
        results = cursor.fetchall()

        if results:
            return [
                {
                    "sid": stu[0],
                    "Name": stu[1],
                    "Department": stu[2],
                    "Semester": stu[3],
                    "CGPA": stu[4],
                    "email": stu[5],
                    "phone": stu[6],
                    "gender": stu[7],
                    "dob": stu[8]
                } for stu in results
            ]
        else:
            return {"status": "Failure", "message": "No students found in this department"}
    finally:
        cursor.close()
        conn.close()

class SemesterItem(BaseModel):
    Semester: int

@app.post("/sem")
def filter_students_by_semester(obj: SemesterItem):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        query = "SELECT * FROM student WHERE Semester = %s"
        cursor.execute(query, (obj.Semester,))
        results = cursor.fetchall()

        if results:
            return [
                {
                    "sid": stu[0],
                    "Name": stu[1],
                    "Department": stu[2],
                    "Semester": stu[3],
                    "CGPA": stu[4],
                    "email": stu[5],
                    "phone": stu[6],
                    "gender": stu[7],
                    "dob": stu[8]
                } for stu in results
            ]
        else:
            return {"status": "Failure", "message": "No students found in this semester"}
    finally:
        cursor.close()
        conn.close()

class CGPAItem(BaseModel):
    CGPA: float

@app.post("/cgpa")
def filter_students_by_cgpa(obj: CGPAItem):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Using a small range for CGPA matching
        query = "SELECT * FROM student WHERE CGPA BETWEEN %s AND %s"
        cursor.execute(query, (obj.CGPA - 0.01, obj.CGPA + 0.01))
        results = cursor.fetchall()

        if not results:
            return {"status": "Failure", "message": "No students found with this CGPA"}

        return [
            {
                "sid": stu[0],
                "Name": stu[1],
                "Department": stu[2],
                "Semester": stu[3],
                "CGPA": stu[4],
                "email": stu[5],
                "phone": stu[6],
                "gender": stu[7],
                "dob": stu[8]
            } for stu in results
        ]
    finally:
        cursor.close()
        conn.close()

class DeleteRequest(BaseModel):
    user_ids: List[str]

@app.delete("/delete")
def delete_users(request: DeleteRequest):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        if not request.user_ids:
            raise HTTPException(status_code=400, detail="No user IDs provided for deletion.")

        format_strings = ','.join(['%s'] * len(request.user_ids))
        query = f"DELETE FROM student WHERE email IN ({format_strings})"
        cursor.execute(query, tuple(request.user_ids))
        conn.commit()

        return {"message": "Users deleted successfully", "deleted_count": cursor.rowcount}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("weblogin:app", host="0.0.0.0", port=8000)
