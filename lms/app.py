from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from datetime import datetime
import uuid

app = Flask(__name__)
app.config["SECRET_KEY"] = "your-secret-key"
app.config["UPLOAD_FOLDER"] = "uploads"
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max upload

# Ensure upload directory exists
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# In-memory database
class MockDB:
    def __init__(self):
        self.collections = {
            "users": [],
            "assignments": [],
            "submissions": [],
            "attendance": [],
            "announcements": [],
            "courses": [],
            "quizzes": [],
            "quiz_results": [],
            "grades": [],
            "enrollments": [],
            "billing": []
        }
        
        # Add sample data
        self._add_sample_data()
        
    def _add_sample_data(self):
        # Sample courses
        self.collections["courses"] = [
            {
                "_id": "1",
                "title": "Introduction to Python",
                "description": "Learn the basics of Python programming language",
                "instructor_name": "John Smith",
                "instructor_id": "1",
                "duration": "8 weeks",
                "is_paid": False,
                "price": 0
            },
            {
                "_id": "2",
                "title": "Advanced Web Development",
                "description": "Master modern web development techniques with React and Node.js",
                "instructor_name": "Jane Doe",
                "instructor_id": "2",
                "duration": "12 weeks",
                "is_paid": True,
                "price": 49.99
            },
            {
                "_id": "3",
                "title": "Data Science Fundamentals",
                "description": "Introduction to data analysis, visualization, and machine learning",
                "instructor_name": "John Smith",
                "instructor_id": "1",
                "duration": "10 weeks",
                "is_paid": True,
                "price": 39.99
            }
        ]
        
        # Sample quizzes
        self.collections["quizzes"] = [
            {
                "_id": "1",
                "title": "Python Basics Quiz",
                "description": "Test your knowledge of Python fundamentals",
                "course_id": "1",
                "teacher_id": "1",
                "difficulty": "easy",
                "question_count": 10,
                "time_limit": 15,
                "points": 100
            },
            {
                "_id": "2",
                "title": "JavaScript Fundamentals",
                "description": "Test your knowledge of JavaScript basics",
                "course_id": "2",
                "teacher_id": "2",
                "difficulty": "medium",
                "question_count": 15,
                "time_limit": 20,
                "points": 150
            },
            {
                "_id": "3",
                "title": "Data Structures Challenge",
                "description": "Hard-level quiz on algorithms and data structures",
                "course_id": "3",
                "teacher_id": "1",
                "difficulty": "hard",
                "question_count": 20,
                "time_limit": 30,
                "points": 200
            }
        ]
        
        # Sample announcements
        self.collections["announcements"] = [
            {
                "_id": "1",
                "title": "Welcome to CodeMaster Academy",
                "content": "Welcome to our learning platform! We're excited to have you join us on this learning journey.",
                "date": datetime.now(),
                "author": "Admin"
            }
        ]
    
    def find_one(self, collection, query):
        for item in self.collections[collection]:
            match = True
            for key, value in query.items():
                if key not in item or item[key] != value:
                    match = False
                    break
            if match:
                return item
        return None
    
    def insert_one(self, collection, document):
        if "_id" not in document:
            document["_id"] = str(uuid.uuid4())
        self.collections[collection].append(document)
        return document["_id"]
    
    def find(self, collection, query=None):
        if query is None:
            return self.collections[collection]
        
        results = []
        for item in self.collections[collection]:
            match = True
            for key, value in query.items():
                if key not in item or item[key] != value:
                    match = False
                    break
            if match:
                results.append(item)
        return results
        
    def update_one(self, collection, query, update):
        for item in self.collections[collection]:
            match = True
            for key, value in query.items():
                if key not in item or item[key] != value:
                    match = False
                    break
            if match:
                for key, value in update.get('$set', {}).items():
                    item[key] = value
                return {'modified_count': 1}
        return {'modified_count': 0}

    def delete_one(self, collection, query):
        for idx, item in enumerate(self.collections[collection]):
            match = True
            for key, value in query.items():
                if key not in item or item[key] != value:
                    match = False
                    break
            if match:
                del self.collections[collection][idx]
                return {'deleted_count': 1}
        return {'deleted_count': 0}

# Initialize mock database
db = MockDB()

# User session management
def login_required(f):
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to access this page", "danger")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# Routes
@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        role = request.form.get("role")
        
        # Validate form data
        if not name or not email or not password or not role:
            flash("All fields are required", "danger")
            return render_template("register.html")
        
        # Check if email already exists
        if db.find_one("users", {"email": email}):
            flash("Email already registered", "danger")
            return render_template("register.html")
        
        # Hash password
        hashed_password = generate_password_hash(password)
        
        # Create user
        user = {
            "name": name,
            "email": email,
            "password": hashed_password,
            "role": role,
            "created_at": datetime.now()
        }
        user_id = db.insert_one("users", user)
        
        # Automatically log in the user after registration
        session["user_id"] = str(user_id)
        session["user_name"] = name
        session["user_role"] = role
        
        flash("Registration successful! Welcome to LMS.", "success")
        return redirect(url_for("dashboard"))
    
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        
        # Find user
        user = db.find_one("users", {"email": email})
        
        if user and check_password_hash(user["password"], password):
            # Store user in session
            session["user_id"] = str(user["_id"])
            session["user_name"] = user["name"]
            session["user_role"] = user["role"]
            
            flash("Login successful!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid email or password", "danger")
    
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out", "info")
    return redirect(url_for("login"))

@app.route("/dashboard")
@login_required
def dashboard():
    user_id = session.get("user_id")
    user = db.find_one("users", {"_id": user_id})
    
    # Get announcements
    announcements = db.find("announcements")[:5]
    
    return render_template("dashboard.html", user=user, announcements=announcements)

@app.route("/profile")
@login_required
def profile():
    user_id = session.get("user_id")
    user = db.find_one("users", {"_id": user_id})
    return render_template("profile.html", user=user)

@app.route("/assignments")
@login_required
def assignments():
    user_id = session.get("user_id")
    user_role = session.get("user_role")
    
    if user_role == "teacher":
        # Teachers see all assignments they created
        assignments = db.find("assignments", {"teacher_id": user_id})
    else:
        # Students see assignments assigned to them
        assignments = db.find("assignments", {"assigned_to": user_id})
    
    return render_template("assignments.html", assignments=assignments, role=user_role)

@app.route("/assignments/create", methods=["GET", "POST"])
@login_required
def create_assignment():
    user_role = session.get("user_role")
    user_id = session.get("user_id")
    if user_role != "teacher":
        flash("Only teachers can create assignments", "danger")
        return redirect(url_for("assignments"))

    if request.method == "POST":
        title = request.form.get("title")
        description = request.form.get("description")
        due_date_str = request.form.get("due_date")
        
        if not title or not description or not due_date_str:
            flash("All fields are required", "danger")
            return redirect(url_for("create_assignment"))

        try:
            due_date = datetime.strptime(due_date_str, "%Y-%m-%d")
        except ValueError:
            flash("Invalid due date format", "danger")
            return redirect(url_for("create_assignment"))

        # Assign to all students: create one assignment entry per student
        students = [u for u in db.find("users") if u.get("role") == "student"]
        for s in students:
            assignment = {
                "title": title,
                "description": description,
                "due_date": due_date,
                "teacher_id": user_id,
                "assigned_to": s.get("_id"),
                "status": "pending",
                "created_at": datetime.now()
            }
            db.insert_one("assignments", assignment)
        flash("Assignment created for all students", "success")
        return redirect(url_for("assignments"))

    return render_template("create_assignment.html")

@app.route("/assignments/upload", methods=["GET", "POST"])
@login_required
def upload_assignment():
    if request.method == "POST":
        assignment_id = request.form.get("assignment_id")
        file = request.files.get("file")
        comments = request.form.get("comments")
        
        if not assignment_id or not file:
            flash("Assignment and file are required", "danger")
            return redirect(url_for("upload_assignment"))
        
        # Save file
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(file_path)
        
        # Save submission
        user_id = session.get("user_id")
        submission = {
            "assignment_id": assignment_id,
            "student_id": user_id,
            "file_path": file_path,
            "comments": comments,
            "submitted_at": datetime.now()
        }
        db.insert_one("submissions", submission)
        
        flash("Assignment submitted successfully", "success")
        return redirect(url_for("assignments"))
    
    # Get assignments for dropdown
    user_id = session.get("user_id")
    assignments = db.find("assignments", {"assigned_to": user_id})
    return render_template("upload_assignment.html", assignments=assignments)

@app.route("/attendance")
@login_required
def attendance():
    user_id = session.get("user_id")
    user_role = session.get("user_role")
    
    if user_role == "teacher":
        # Teachers see attendance records they've taken
        attendance_records = db.find("attendance", {"teacher_id": user_id})
    else:
        # Students see their own attendance
        attendance_records = db.find("attendance", {"student_id": user_id})
    
    return render_template("attendance.html", attendance=attendance_records, role=user_role)

@app.route("/announcements")
@login_required
def announcements():
    announcements = db.find("announcements")
    return render_template("announcements.html", announcements=announcements, role=session.get("user_role"))

@app.route("/courses")
@login_required
def courses():
    # Get all available courses
    all_courses = db.find("courses")
    # Get enrolled courses for current user
    user_id = session.get("user_id")
    enrolled_courses = db.find("enrollments", {"student_id": user_id})
    enrolled_ids = [course["course_id"] for course in enrolled_courses]
    
    return render_template("courses.html", 
                          courses=all_courses, 
                          enrolled_ids=enrolled_ids,
                          role=session.get("user_role"))

@app.route("/courses/enroll/<course_id>")
@login_required
def enroll_course(course_id):
    user_id = session.get("user_id")
    # Check if course is paid
    course = db.find_one("courses", {"_id": course_id})
    
    if course and course.get("is_paid", False):
        # Redirect to payment page for paid courses
        return redirect(url_for("billing", course_id=course_id))
    
    # Check if already enrolled
    existing_enrollment = db.find_one("enrollments", {"student_id": user_id, "course_id": course_id})
    if existing_enrollment:
        flash("You are already enrolled in this course", "info")
        return redirect(url_for("courses"))
    
    # Enroll in free course
    db.insert_one("enrollments", {
        "student_id": user_id,
        "course_id": course_id,
        "enrolled_at": datetime.now()
    })
    
    flash("Successfully enrolled in the course!", "success")
    return redirect(url_for("courses"))

@app.route("/quizzes")
@login_required
def quizzes():
    user_id = session.get("user_id")
    user_role = session.get("user_role")
    selected_course_id = request.args.get("course_id")
    
    if user_role == "teacher":
        # Teachers see all quizzes they created
        quizzes = db.find("quizzes", {"teacher_id": user_id})
        teacher_courses = db.find("courses", {"instructor_id": user_id})
        if selected_course_id:
            quizzes = [q for q in quizzes if q.get("course_id") == selected_course_id]
    else:
        # Students see quizzes for courses they're enrolled in
        enrollments = db.find("enrollments", {"student_id": user_id})
        course_ids = [enrollment["course_id"] for enrollment in enrollments]
        quizzes = []
        for course_id in course_ids:
            course_quizzes = db.find("quizzes", {"course_id": course_id})
            quizzes.extend(course_quizzes)
        if selected_course_id:
            quizzes = [q for q in quizzes if q.get("course_id") == selected_course_id]
    
    # Filter by difficulty
    easy_quizzes = [q for q in quizzes if q.get("difficulty") == "easy"]
    medium_quizzes = [q for q in quizzes if q.get("difficulty") == "medium"]
    hard_quizzes = [q for q in quizzes if q.get("difficulty") == "hard"]
    
    context = {
        "quizzes": quizzes,
        "easy_quizzes": easy_quizzes,
        "medium_quizzes": medium_quizzes,
        "hard_quizzes": hard_quizzes,
        "role": user_role
    }
    if user_role == "teacher":
        context["teacher_courses"] = db.find("courses", {"instructor_id": user_id})
    context["selected_course_id"] = selected_course_id
    return render_template("quizzes.html", **context)

@app.route("/quizzes/add", methods=["POST"])
@login_required
def add_quiz():
    if session.get("user_role") != "teacher":
        flash("Only teachers can add quizzes", "danger")
        return redirect(url_for("quizzes"))

    title = request.form.get("title")
    description = request.form.get("description")
    difficulty = request.form.get("difficulty")
    question_count = int(request.form.get("question_count") or 0)
    time_limit = int(request.form.get("time_limit") or 0)
    points = int(request.form.get("points") or 0)
    course_id = request.form.get("course_id")

    if not title or not description or not difficulty or not question_count or not time_limit or not points or not course_id:
        flash("All fields are required", "danger")
        return redirect(url_for("quizzes"))

    db.insert_one("quizzes", {
        "title": title,
        "description": description,
        "difficulty": difficulty,
        "question_count": question_count,
        "time_limit": time_limit,
        "points": points,
        "course_id": course_id,
        "teacher_id": session.get("user_id")
    })
    flash("Quiz created", "success")
    return redirect(url_for("quizzes"))

@app.route("/quizzes/start/<quiz_id>")
@login_required
def start_quiz(quiz_id):
    # Minimal mock: immediately record a perfect score and log a grade
    user_role = session.get("user_role")
    if user_role != "student":
        flash("Only students can take quizzes", "danger")
        return redirect(url_for("quizzes"))

    quiz = db.find_one("quizzes", {"_id": quiz_id})
    if not quiz:
        flash("Quiz not found", "danger")
        return redirect(url_for("quizzes"))

    # Record result
    result = {
        "quiz_id": quiz_id,
        "student_id": session.get("user_id"),
        "score": 100,
        "points_earned": quiz.get("points", 0),
        "total_points": quiz.get("points", 0),
        "date_taken": datetime.now()
    }
    db.insert_one("quiz_results", result)

    # Also add to grades
    course = db.find_one("courses", {"_id": quiz.get("course_id")}) or {}
    db.insert_one("grades", {
        "category": "quiz",
        "quiz_title": quiz.get("title"),
        "course_title": course.get("title", "Unknown Course"),
        "difficulty": quiz.get("difficulty"),
        "score": 100,
        "points_earned": quiz.get("points", 0),
        "total_points": quiz.get("points", 0),
        "date_taken": datetime.now(),
        "student_id": session.get("user_id")
    })

    flash("Quiz completed! Score recorded.", "success")
    return redirect(url_for("grades"))

@app.route("/grades")
@login_required
def grades():
    user_id = session.get("user_id")
    user_role = session.get("user_role")
    
    # Fetch raw grade records (if any)
    if user_role == "teacher":
        grade_records = db.find("grades", {"teacher_id": user_id})
    else:
        grade_records = db.find("grades", {"student_id": user_id})
    
    # Split into categories expected by the template
    course_grades = [g for g in grade_records if g.get("category") == "course"]
    quiz_grades = [g for g in grade_records if g.get("category") == "quiz"]
    assignment_grades = [g for g in grade_records if g.get("category") == "assignment"]
    
    # If no records present, provide demo data to avoid template errors
    if not course_grades:
        course_grades = [
            {
                "course_title": "Introduction to Python",
                "instructor_name": "John Smith",
                "overall_grade": 85
            },
            {
                "course_title": "Web Development",
                "instructor_name": "Jane Doe",
                "overall_grade": 92
            }
        ]
    if not quiz_grades:
        quiz_grades = [
            {
                "quiz_title": "Python Basics",
                "course_title": "Introduction to Python",
                "difficulty": "easy",
                "score": 90,
                "points_earned": 90,
                "total_points": 100,
                "date_taken": "2023-06-15"
            },
            {
                "quiz_title": "JavaScript Fundamentals",
                "course_title": "Advanced Web Development",
                "difficulty": "medium",
                "score": 78,
                "points_earned": 117,
                "total_points": 150,
                "date_taken": "2023-06-18"
            }
        ]
    if not assignment_grades:
        assignment_grades = [
            {
                "assignment_title": "Python Functions",
                "course_title": "Introduction to Python",
                "grade": 85,
                "feedback": "Good work, but could improve code organization",
                "submission_date": "2023-06-10"
            },
            {
                "assignment_title": "React Components",
                "course_title": "Advanced Web Development",
                "grade": 88,
                "feedback": "Solid component structure",
                "submission_date": "2023-06-12"
            }
        ]
    
    return render_template(
        "grades.html",
        role=user_role,
        course_grades=course_grades,
        quiz_grades=quiz_grades,
        assignment_grades=assignment_grades
    )

@app.route("/billing", methods=["GET", "POST"])
@login_required
def billing():
    user_id = session.get("user_id")
    course_id = request.args.get("course_id")
    
    if request.method == "POST":
        # Process payment (mock)
        payment_successful = True
        
        if payment_successful:
            # Enroll student after payment
            db.insert_one("enrollments", {
                "student_id": user_id,
                "course_id": course_id,
                "enrolled_at": datetime.now(),
                "payment_status": "paid"
            })
            
            flash("Payment successful! You are now enrolled in the course.", "success")
            return redirect(url_for("courses"))
        else:
            flash("Payment failed. Please try again.", "danger")
    
    # Get course details if course_id is provided
    course = None
    if course_id:
        course = db.find_one("courses", {"_id": course_id})
    
    # Get all billing records for the user
    billing_records = db.find("billing", {"student_id": user_id})

    # Map to template variables with safe defaults
    payments = [
        {
            "date": r.get("date", datetime.now().strftime("%Y-%m-%d")),
            "description": r.get("description", "Course Payment"),
            "amount": r.get("amount", 0),
            "status": r.get("status", "completed")
        }
        for r in billing_records
        if r.get("type", "payment") == "payment"
    ]

    upcoming_payments = [
        {
            "_id": r.get("_id", str(uuid.uuid4())),
            "due_date": r.get("due_date", datetime.now().strftime("%Y-%m-%d")),
            "description": r.get("description", "Upcoming Payment"),
            "amount": r.get("amount", 0)
        }
        for r in billing_records
        if r.get("type") == "upcoming"
    ]

    total_paid = sum(p.get("amount", 0) for p in payments if p.get("status") == "completed")
    pending_amount = sum(p.get("amount", 0) for p in upcoming_payments)
    balance = pending_amount - total_paid if (pending_amount - total_paid) > 0 else 0

    payment_methods = db.find("billing", {"student_id": user_id, "type": "method"})

    return render_template(
        "billing.html",
        course=course,
        payments=payments,
        upcoming_payments=upcoming_payments,
        total_paid=total_paid,
        pending_amount=pending_amount,
        balance=balance,
        payment_methods=payment_methods
    )

@app.route("/process_payment", methods=["POST"])
@login_required
def process_payment():
    # Mock payment processing
    flash("Payment processed successfully.", "success")
    return redirect(url_for("billing"))

@app.route("/add_payment_method", methods=["POST"])
@login_required
def add_payment_method():
    user_id = session.get("user_id")
    method_type = request.form.get("method_type")
    name = "Card" if method_type == "card" else "Bank Account"
    db.insert_one("billing", {
        "student_id": user_id,
        "type": "method",
        "name": name,
        "created_at": datetime.now()
    })
    flash("Payment method added.", "success")
    return redirect(url_for("billing"))

@app.route("/add_course", methods=["POST"])
@login_required
def add_course():
    if session.get("user_role") != "teacher":
        flash("Only teachers can add courses", "danger")
        return redirect(url_for("courses"))

    title = request.form.get("title")
    description = request.form.get("description")
    duration = request.form.get("duration")
    is_paid = True if request.form.get("is_paid") == "on" else False
    price = float(request.form.get("price") or 0)

    if not title or not description or not duration:
        flash("All fields are required", "danger")
        return redirect(url_for("courses"))

    db.insert_one("courses", {
        "title": title,
        "description": description,
        "duration": duration,
        "is_paid": is_paid,
        "price": price,
        "instructor_name": session.get("user_name"),
        "instructor_id": session.get("user_id")
    })
    flash("Course created", "success")
    return redirect(url_for("courses"))

@app.route("/courses/<course_id>/edit", methods=["POST"])
@login_required
def edit_course(course_id):
    if session.get("user_role") != "teacher":
        flash("Only teachers can manage courses", "danger")
        return redirect(url_for("courses"))

    course = db.find_one("courses", {"_id": course_id})
    if not course or course.get("instructor_id") != session.get("user_id"):
        flash("You can only edit your own courses", "danger")
        return redirect(url_for("courses"))

    title = request.form.get("title")
    description = request.form.get("description")
    duration = request.form.get("duration")
    is_paid = True if request.form.get("is_paid") == "on" else False
    price = float(request.form.get("price") or 0)

    update_fields = {}
    if title: update_fields["title"] = title
    if description: update_fields["description"] = description
    if duration: update_fields["duration"] = duration
    update_fields["is_paid"] = is_paid
    update_fields["price"] = price

    db.update_one("courses", {"_id": course_id}, {"$set": update_fields})
    flash("Course updated", "success")
    return redirect(url_for("courses"))

@app.route("/courses/<course_id>/delete", methods=["POST"])
@login_required
def delete_course(course_id):
    if session.get("user_role") != "teacher":
        flash("Only teachers can delete courses", "danger")
        return redirect(url_for("courses"))

    course = db.find_one("courses", {"_id": course_id})
    if not course or course.get("instructor_id") != session.get("user_id"):
        flash("You can only delete your own courses", "danger")
        return redirect(url_for("courses"))

    db.delete_one("courses", {"_id": course_id})
    flash("Course deleted", "success")
    return redirect(url_for("courses"))

@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email")
        new_password = request.form.get("new_password")
        confirm_password = request.form.get("confirm_password")

        if not email or not new_password or not confirm_password:
            flash("All fields are required", "danger")
            return render_template("forgot_password.html")

        if new_password != confirm_password:
            flash("Passwords do not match", "danger")
            return render_template("forgot_password.html")
        
        # Check if email exists
        user = db.find_one("users", {"email": email})
        if not user:
            flash("Email not found", "danger")
            return render_template("forgot_password.html")
        
        # Update user password
        hashed_password = generate_password_hash(new_password)
        user["password"] = hashed_password
        
        flash("Password updated successfully. Please login.", "success")
        return redirect(url_for("login"))
    
    return render_template("forgot_password.html")

@app.route("/update_profile", methods=["POST"])
@login_required
def update_profile():
    user_id = session.get("user_id")
    name = request.form.get("name")
    email = request.form.get("email")
    phone = request.form.get("phone")
    address = request.form.get("address")
    roll_no = request.form.get("roll_no")

    update_fields = {}
    if name:
        update_fields["name"] = name
    if email:
        update_fields["email"] = email
    if phone:
        update_fields["phone"] = phone
    if address:
        update_fields["address"] = address
    if roll_no:
        update_fields["roll_no"] = roll_no

    if update_fields:
        db.update_one("users", {"_id": user_id}, {"$set": update_fields})
        # Keep session name in sync for header
        if name:
            session["user_name"] = name
        flash("Profile updated successfully", "success")
    else:
        flash("No changes provided", "warning")

    return redirect(url_for("profile"))

if __name__ == "__main__":
    app.run(debug=True)