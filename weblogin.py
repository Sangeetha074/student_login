import mysql.connector
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from typing import List

app = FastAPI()

# Configure CORS to handle all origins for local testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Allow all origins for testing (Adjust for production)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# host = "http://srv1834.hstgr.io/",
# user = "u651328475_fastapi",
# password = "U651328475_fastapi",
# database = "u651328475_fastapi",
# Database connection function
def get_db_connection():
    connection = mysql.connector.connect(

      # host="localhost",
      # user="root",
      # password="",
      # database="registration",
      # port=3306,
      # use_pure=True
      host = "auth-db1834.hstgr.io",
      user = "u651328475_fastapi",
      password = "U651328475_fastapi",
      database = "u651328475_fastapi",
      use_pure=True
    )
    # if connection.is_connected():
    #     print("database connected")
    # else:
    #     print("database not connected")
    return connection




# Basic Authentication setup
security = HTTPBasic()
VALID_USERNAME = "Ram"
VALID_PASSWORD = "1234"


def basic_auth(credentials: HTTPBasicCredentials = Depends(security)):
    if credentials.username != VALID_USERNAME or credentials.password != VALID_PASSWORD:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=" username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username
@app.post("/data")
def  get_secure_data(username:str=Depends(basic_auth)):
    return {
        "message":"access granted",
        "username":username,
    }


# Pydantic models for input validation
class Item(BaseModel):
    username: str
    password: str


# User login verification from the 'userinform' table
@app.post("/reg")
def read_root2(obj: Item):
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM userinform")
    myresult = cursor.fetchall()
    print(f"Received: username={obj.username}, password={obj.password}")
    for row in myresult:
        db_username = row[1]  # change index as per actual column order
        db_password = row[2]  # change index as per actual column order
        print(f"Comparing with DB: username={db_username}, password={db_password}")
        if obj.username.strip() == db_username.strip() and obj.password.strip() == str(db_password).strip():


            return {"status": "Success", "message": "Login successful"}

    return {"status": "Failure", "message": "username or password"}
# def reg(obj: Item):
#     conn = get_db_connection()
#     cursor = conn.cursor()
#
#     cursor.execute("SELECT * FROM userinform WHERE TRIM(username) = %s AND TRIM(password) = %s",
#                    (obj.username.strip(), obj.password.strip()))
#     user = cursor.fetchone()
#
#     conn.close()
#
#     if user:
#         return {"status": "Success", "message": "Login successful"}
#
#     else:
#         raise HTTPException(status_code=400, detail="username or password")


# Basic authentication secured route
@app.post("/num")
def get_secure_data(username: str = Depends(basic_auth)):
    return {"message": "Access granted", "username": username}


# Insert user into 'userinform' table
@app.post("/insert")
def insert_data(user: Item):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        query = "INSERT INTO userinform (username, password) VALUES (%s, %s)"
        values = (user.username, user.password)
        cursor.execute(query, values)
        conn.commit()
        return {"message": "Data inserted successfully", "data": user}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to insert data: {str(e)}")
    finally:
        cursor.close()
        conn.close()


# Forgot password functionality
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
        raise HTTPException(status_code=404, detail="User not found")

    cursor.execute("UPDATE userinform SET password = %s WHERE username = %s", (request.new_password, request.username))
    conn.commit()
    conn.close()

    return {"status": "Success", "message": "Password updated successfully"}


# Fetch all users from 'userinform' table
@app.get("/usersinform")
def get_users():
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT * FROM userinform")
        users = cursor.fetchall()
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


# Register a student
@app.post("/stform")
def register_student(student: Student):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Check if email or phone already exists
        cursor.execute("SELECT * FROM student WHERE email = %s OR phone = %s", (student.email, student.phone))
        existing_student = cursor.fetchone()

        if existing_student:
            raise HTTPException(status_code=400, detail="Email or phone already registered")

        # Insert new student
        query = """
        INSERT INTO student (Name, email, phone, dob, gender, Department, Semester, CGPA) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        values = (
        student.Name, student.email, student.phone, student.dob, student.gender, student.Department, student.Semester,
        student.CGPA)
        cursor.execute(query, values)
        conn.commit()
        return {"message": "Student registered successfully"}

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to register student: {str(e)}")

    finally:
        cursor.close()
        conn.close()


# Search students
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
        WHERE Name LIKE %s OR email LIKE %s OR phone LIKE %s OR Department LIKE %s OR Semester  LIKE %s OR CGPA  LIKE %s
        """
        cursor.execute(sql_query, (search_term, search_term, search_term, search_term, search_term, search_term))
        results = cursor.fetchall()
        print(results)
        return [{"sid": stu[0], "Name": stu[1], "email": stu[5], "phone": stu[6], "dob": stu[8], "gender": stu[7],
                 "Department": stu[2], "Semester": stu[3], "CGPA": stu[4]} for stu in results]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        cursor.close()
        conn.close()


# Filter students by department
class DepartmentItem(BaseModel):
    Department: str


@app.post("/dep")
def filter_students_by_department(obj: DepartmentItem):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        query = "SELECT * FROM student WHERE Department= %s"
        cursor.execute(query, (obj.Department,))
        results = cursor.fetchall()

        return [{"sid": stu[0], "Name": stu[1], "email": stu[5], "phone": stu[6], "dob": stu[8], "gender": stu[7],
                 "Department": stu[2], "Semester": stu[3], "CGPA": stu[4]} for stu in results]if results else {"status": "Failure", "message": "No students found in this department"}

    finally:
        cursor.close()
        conn.close()


# Filter students by semester
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

        return [{"sid": stu[0], "Name": stu[1], "email": stu[5], "phone": stu[6], "dob": stu[8], "gender": stu[7],
                 "Department": stu[2], "Semester": stu[3], "CGPA": stu[4]} for stu in results] if results else {"status": "Failure", "message": "No students found in this semester"}

    finally:
        cursor.close()
        conn.close()


# Filter students by CGPA
class CGPAItem(BaseModel):
    CGPA:float



@app.post("/cgpa")
def filter_students_by_cgpa(obj: CGPAItem):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        query = "SELECT * FROM student WHERE CGPA BETWEEN %s AND %s"
        cursor.execute(query, (obj.CGPA - 0.01, obj.CGPA + 0.01))

        results = cursor.fetchall()
        print(f"Executed Query: {query} with CGPA=({obj.CGPA - 0.01}, {obj.CGPA + 0.01})")
        print(f"Query Results: {results}")

        if not results:
            return {"status": "Failure", "message": "No students found with this CGPA"}


        return [{"sid": stu[0], "Name": stu[1], "email": stu[5], "phone": stu[6], "dob": stu[8], "gender": stu[7],
                 "Department": stu[2], "Semester": stu[3], "CGPA": stu[4]} for stu in results] if results else {"status": "Failure", "message": "No students found with this CGPA"}

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

        # Convert list of IDs into a comma-separated string for SQL
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
if __name__== "__main__":
    import uvicorn
    uvicorn.run("weblogin:app", host="0.0.0.0", port=8000)
    #done

# Search users by various fields
# class SearchQuery(BaseModel):
#     search: str
#
#
# @app.post("/search")
# def search_users(query: SearchQuery):
#     conn = get_db_connection()
#     cursor = conn.cursor()
#
#     try:
#         search_term = f"%{query.search}%"
#         sql_query = """
#         SELECT * FROM student
#         WHERE name LIKE %s
#         OR sid LIKE %s
#         OR Department LIKE %s
#         OR semester LIKE %s
#         OR CGPA LIKE %s
#         """
#         cursor.execute(sql_query, (search_term, search_term, search_term, search_term, search_term))
#         results = cursor.fetchall()
#
#         if not results:
#             return []
#
#         return [{"sid": user[0], "name": user[1], "Department": user[2], "semester": user[3], "CGPA": user[4]} for user
#                 in results]
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))
#     finally:
#         cursor.close()
#         conn.close()
#
#
# # Filter users by department
# class DepartmentItem(BaseModel):
#     Department: str
#
#
# @app.post("/dep")
# def post_users_by_department(obj: DepartmentItem):
#     conn = get_db_connection()
#     cursor = conn.cursor()
#
#     try:
#         query = "SELECT * FROM student WHERE Department = %s"
#         cursor.execute(query, (obj.Department,))
#         results = cursor.fetchall()
#
#         if results:
#             return [{"sid": user[0], "name": user[1], "Department": user[2], "semester": user[3], "CGPA": user[4]} for
#                     user in results]
#         else:
#             return {"status": "Failure", "message": "No users found in the specified department"}
#     finally:
#         cursor.close()
#         conn.close()
#
#
# # Filter users by semester
# class SemesterItem(BaseModel):
#     semester: str
#
#
# @app.post("/sem")
# def post_users_by_semester(obj: SemesterItem):
#     conn = get_db_connection()
#     cursor = conn.cursor()
#
#     try:
#         query = "SELECT * FROM student WHERE semester = %s"
#         cursor.execute(query, (obj.semester,))
#         results = cursor.fetchall()
#
#         if results:
#             return [{"sid": user[0], "name": user[1], "Department": user[2], "semester": user[3], "CGPA": user[4]} for
#                     user in results]
#         else:
#             return {"status": "Failure", "message": "No users found in the specified semester"}
#     finally:
#         cursor.close()
#         conn.close()
#
#
# # Filter users by CGPA
# class CGPAItem(BaseModel):
#     CGPA: float
#
#
# @app.post("/cgpa")
# def post_users_by_cgpa(obj: CGPAItem):
#     conn = get_db_connection()
#     cursor = conn.cursor()
#
#     try:
#         query = "SELECT * FROM student WHERE TRIM(CGPA) = %s"
#         cursor.execute(query, (obj.CGPA,))
#         results = cursor.fetchall()
#
#         if results:
#             return [{"sid": user[0], "name": user[1], "Department": user[2], "semester": user[3], "CGPA": user[4]} for
#                     user in results]
#         else:
#             return {"status": "Failure", "message": "No users found with the specified CGPA"}
#     finally:
#         cursor.close()
#         conn.close()