import sqlite3
import logging

logger = logging.getLogger(__name__)

def generate_college_erp_db(db_path: str):
    """Generates a SQLite database containing 22 interrelated operational tables for College ERP."""
    logger.info(f"Generating College ERP database at: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")

    # Table 1: departments
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS departments (
        dept_id INTEGER PRIMARY KEY AUTOINCREMENT,
        dept_name TEXT NOT NULL,
        code TEXT UNIQUE NOT NULL,
        budget REAL NOT NULL,
        head_id INTEGER
    );
    """)

    # Table 2: programs
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS programs (
        program_id INTEGER PRIMARY KEY AUTOINCREMENT,
        program_name TEXT NOT NULL,
        dept_id INTEGER,
        duration_years INTEGER NOT NULL,
        total_credits INTEGER NOT NULL,
        FOREIGN KEY (dept_id) REFERENCES departments(dept_id)
    );
    """)

    # Table 3: students
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS students (
        student_id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        date_of_birth TEXT NOT NULL,
        enrollment_date TEXT NOT NULL,
        status TEXT NOT NULL,
        program_id INTEGER,
        FOREIGN KEY (program_id) REFERENCES programs(program_id)
    );
    """)

    # Table 4: instructors
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS instructors (
        instructor_id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        phone TEXT,
        hire_date TEXT NOT NULL,
        status TEXT NOT NULL,
        dept_id INTEGER,
        FOREIGN KEY (dept_id) REFERENCES departments(dept_id)
    );
    """)

    # Table 5: courses
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS courses (
        course_id INTEGER PRIMARY KEY AUTOINCREMENT,
        course_title TEXT NOT NULL,
        course_code TEXT UNIQUE NOT NULL,
        credits INTEGER NOT NULL,
        dept_id INTEGER,
        FOREIGN KEY (dept_id) REFERENCES departments(dept_id)
    );
    """)

    # Table 6: classrooms
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS classrooms (
        classroom_id INTEGER PRIMARY KEY AUTOINCREMENT,
        room_number TEXT UNIQUE NOT NULL,
        building TEXT NOT NULL,
        capacity INTEGER NOT NULL,
        room_type TEXT NOT NULL
    );
    """)

    # Table 7: sections
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sections (
        section_id INTEGER PRIMARY KEY AUTOINCREMENT,
        course_id INTEGER,
        instructor_id INTEGER,
        classroom_id INTEGER,
        semester TEXT NOT NULL,
        academic_year INTEGER NOT NULL,
        schedule_pattern TEXT NOT NULL,
        FOREIGN KEY (course_id) REFERENCES courses(course_id),
        FOREIGN KEY (instructor_id) REFERENCES instructors(instructor_id),
        FOREIGN KEY (classroom_id) REFERENCES classrooms(classroom_id)
    );
    """)

    # Table 8: enrollments
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS enrollments (
        enrollment_id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        section_id INTEGER,
        enrollment_date TEXT NOT NULL,
        status TEXT NOT NULL,
        grade_points REAL,
        FOREIGN KEY (student_id) REFERENCES students(student_id),
        FOREIGN KEY (section_id) REFERENCES sections(section_id)
    );
    """)

    # Table 9: attendance
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS attendance (
        attendance_id INTEGER PRIMARY KEY AUTOINCREMENT,
        enrollment_id INTEGER,
        class_date TEXT NOT NULL,
        status TEXT NOT NULL,
        FOREIGN KEY (enrollment_id) REFERENCES enrollments(enrollment_id)
    );
    """)

    # Table 10: grades
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS grades (
        grade_id INTEGER PRIMARY KEY AUTOINCREMENT,
        enrollment_id INTEGER,
        assessment_name TEXT NOT NULL,
        max_marks INTEGER NOT NULL,
        marks_obtained REAL NOT NULL,
        weightage_percent INTEGER NOT NULL,
        FOREIGN KEY (enrollment_id) REFERENCES enrollments(enrollment_id)
    );
    """)

    # Table 11: advising_records
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS advising_records (
        advising_id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        instructor_id INTEGER,
        advising_date TEXT NOT NULL,
        notes TEXT,
        FOREIGN KEY (student_id) REFERENCES students(student_id),
        FOREIGN KEY (instructor_id) REFERENCES instructors(instructor_id)
    );
    """)

    # Table 12: tuition_fees
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tuition_fees (
        fee_id INTEGER PRIMARY KEY AUTOINCREMENT,
        program_id INTEGER,
        semester TEXT NOT NULL,
        amount REAL NOT NULL,
        billing_category TEXT NOT NULL,
        FOREIGN KEY (program_id) REFERENCES programs(program_id)
    );
    """)

    # Table 13: student_accounts
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS student_accounts (
        account_id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        balance REAL NOT NULL,
        status TEXT NOT NULL,
        FOREIGN KEY (student_id) REFERENCES students(student_id)
    );
    """)

    # Table 14: transactions
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
        account_id INTEGER,
        amount REAL NOT NULL,
        transaction_type TEXT NOT NULL,
        transaction_date TEXT NOT NULL,
        payment_method TEXT NOT NULL,
        FOREIGN KEY (account_id) REFERENCES student_accounts(account_id)
    );
    """)

    # Table 15: scholarships
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS scholarships (
        scholarship_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        amount_percent INTEGER NOT NULL,
        criteria TEXT
    );
    """)

    # Table 16: student_scholarships
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS student_scholarships (
        student_id INTEGER,
        scholarship_id INTEGER,
        awarded_date TEXT NOT NULL,
        status TEXT NOT NULL,
        PRIMARY KEY (student_id, scholarship_id),
        FOREIGN KEY (student_id) REFERENCES students(student_id),
        FOREIGN KEY (scholarship_id) REFERENCES scholarships(scholarship_id)
    );
    """)

    # Table 17: hostels
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS hostels (
        hostel_id INTEGER PRIMARY KEY AUTOINCREMENT,
        hostel_name TEXT UNIQUE NOT NULL,
        address TEXT,
        warden_name TEXT,
        total_rooms INTEGER NOT NULL
    );
    """)

    # Table 18: hostel_allotments
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS hostel_allotments (
        allotment_id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        hostel_id INTEGER,
        room_number TEXT NOT NULL,
        allotment_date TEXT NOT NULL,
        check_out_date TEXT,
        FOREIGN KEY (student_id) REFERENCES students(student_id),
        FOREIGN KEY (hostel_id) REFERENCES hostels(hostel_id)
    );
    """)

    # Table 19: library_books
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS library_books (
        book_id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        author TEXT NOT NULL,
        isbn TEXT UNIQUE NOT NULL,
        category TEXT NOT NULL,
        total_copies INTEGER NOT NULL,
        available_copies INTEGER NOT NULL
    );
    """)

    # Table 20: book_loans
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS book_loans (
        loan_id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        book_id INTEGER,
        checkout_date TEXT NOT NULL,
        return_date TEXT,
        status TEXT NOT NULL,
        fine_amount REAL DEFAULT 0.0,
        FOREIGN KEY (student_id) REFERENCES students(student_id),
        FOREIGN KEY (book_id) REFERENCES library_books(book_id)
    );
    """)

    # Table 21: staff
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS staff (
        staff_id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        job_title TEXT NOT NULL,
        salary REAL NOT NULL,
        hire_date TEXT NOT NULL,
        dept_id INTEGER,
        FOREIGN KEY (dept_id) REFERENCES departments(dept_id)
    );
    """)

    # Table 22: assets
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS assets (
        asset_id INTEGER PRIMARY KEY AUTOINCREMENT,
        asset_name TEXT NOT NULL,
        asset_type TEXT NOT NULL,
        purchase_date TEXT NOT NULL,
        purchase_cost REAL NOT NULL,
        status TEXT NOT NULL,
        location_classroom_id INTEGER,
        FOREIGN KEY (location_classroom_id) REFERENCES classrooms(classroom_id)
    );
    """)

    # Populate Sample Records (Insert only if database is empty)
    cursor.execute("SELECT COUNT(*) FROM departments;")
    if cursor.fetchone()[0] == 0:
        logger.info("Inserting sample ERP records into SQLite database...")
        
        # 1. departments
        depts = [
            (1, 'Computer Science', 'CS', 1200000.0, 1),
            (2, 'Electrical Engineering', 'EE', 950000.0, 3),
            (3, 'Mechanical Engineering', 'ME', 800000.0, None),
            (4, 'Mathematics', 'MA', 500000.0, 4)
        ]
        cursor.executemany("INSERT INTO departments VALUES (?, ?, ?, ?, ?);", depts)

        # 2. programs
        programs = [
            (1, 'BS Computer Science', 1, 4, 120),
            (2, 'MS Cybersecurity', 1, 2, 60),
            (3, 'BE Electrical Engineering', 2, 4, 128),
            (4, 'PhD Mathematics', 4, 5, 90)
        ]
        cursor.executemany("INSERT INTO programs VALUES (?, ?, ?, ?, ?);", programs)

        # 3. students
        students = [
            (1, 'John', 'Doe', 'john.doe@university.edu', '2002-04-12', '2021-09-01', 'Active', 1),
            (2, 'Jane', 'Smith', 'jane.smith@university.edu', '2001-08-22', '2020-09-01', 'Active', 1),
            (3, 'Alice', 'Johnson', 'alice.johnson@university.edu', '2003-01-15', '2022-09-01', 'Active', 3),
            (4, 'Bob', 'Brown', 'bob.brown@university.edu', '1999-05-30', '2021-09-01', 'Suspended', 2),
            (5, 'Charlie', 'Davis', 'charlie.davis@university.edu', '2004-11-05', '2023-09-01', 'Active', 1),
            (6, 'Diana', 'Evans', 'diana.evans@university.edu', '2000-02-18', '2019-09-01', 'Graduated', 4)
        ]
        cursor.executemany("INSERT INTO students VALUES (?, ?, ?, ?, ?, ?, ?, ?);", students)

        # 4. instructors
        instructors = [
            (1, 'Alan', 'Turing', 'alan.turing@university.edu', '555-0101', '2010-08-15', 'Active', 1),
            (2, 'Claude', 'Shannon', 'claude.shannon@university.edu', '555-0102', '2012-01-10', 'Active', 1),
            (3, 'Nikola', 'Tesla', 'nikola.tesla@university.edu', '555-0103', '2015-08-20', 'Active', 2),
            (4, 'Emmy', 'Noether', 'emmy.noether@university.edu', '555-0104', '2008-09-01', 'Active', 4),
            (5, 'Richard', 'Feynman', 'richard.feynman@university.edu', '555-0105', '2018-03-15', 'On Leave', 2)
        ]
        cursor.executemany("INSERT INTO instructors VALUES (?, ?, ?, ?, ?, ?, ?, ?);", instructors)

        # 5. courses
        courses = [
            (1, 'Introduction to Programming', 'CS101', 4, 1),
            (2, 'Data Structures & Algorithms', 'CS201', 4, 1),
            (3, 'Computer Networks', 'CS305', 3, 1),
            (4, 'Introduction to Cybersecurity', 'CS402', 3, 1),
            (5, 'Circuit Analysis', 'EE101', 4, 2),
            (6, 'Linear Algebra', 'MA201', 3, 4),
            (7, 'Advanced Calculus', 'MA301', 4, 4)
        ]
        cursor.executemany("INSERT INTO courses VALUES (?, ?, ?, ?, ?);", courses)

        # 6. classrooms
        classrooms = [
            (1, '301', 'Main Building', 60, 'Lecture Hall'),
            (2, '102', 'Engineering Block', 40, 'Lab'),
            (3, '405', 'Science Center', 120, 'Auditorium'),
            (4, '204', 'Math Annex', 30, 'Seminar Room')
        ]
        cursor.executemany("INSERT INTO classrooms VALUES (?, ?, ?, ?, ?);", classrooms)

        # 7. sections
        sections = [
            (1, 1, 1, 1, 'Fall', 2025, 'MWF 09:00-10:00'),
            (2, 1, 2, 2, 'Fall', 2025, 'TTh 10:30-12:00'),
            (3, 2, 1, 1, 'Spring', 2026, 'MWF 11:00-12:00'),
            (4, 5, 3, 2, 'Fall', 2025, 'TTh 14:00-15:30'),
            (5, 6, 4, 4, 'Fall', 2025, 'MWF 13:00-14:00')
        ]
        cursor.executemany("INSERT INTO sections VALUES (?, ?, ?, ?, ?, ?, ?);", sections)

        # 8. enrollments
        enrollments = [
            (1, 1, 1, '2025-08-25', 'Completed', 4.0),
            (2, 2, 1, '2025-08-25', 'Completed', 3.7),
            (3, 5, 1, '2025-08-25', 'Completed', 3.0),
            (4, 1, 3, '2026-01-10', 'Active', None),
            (5, 2, 3, '2026-01-10', 'Active', None),
            (6, 3, 4, '2025-08-26', 'Completed', 3.3),
            (7, 3, 5, '2025-08-26', 'Completed', 4.0),
            (8, 1, 5, '2025-08-26', 'Completed', 3.7)
        ]
        cursor.executemany("INSERT INTO enrollments VALUES (?, ?, ?, ?, ?, ?);", enrollments)

        # 9. attendance
        attendance = [
            (1, 1, '2025-09-01', 'Present'),
            (2, 1, '2025-09-03', 'Present'),
            (3, 1, '2025-09-05', 'Absent'),
            (4, 1, '2025-09-08', 'Present'),
            (5, 1, '2025-09-10', 'Present'),
            (6, 2, '2025-09-01', 'Present'),
            (7, 2, '2025-09-03', 'Present'),
            (8, 2, '2025-09-05', 'Present'),
            (9, 2, '2025-09-08', 'Present'),
            (10, 2, '2025-09-10', 'Present')
        ]
        cursor.executemany("INSERT INTO attendance VALUES (?, ?, ?, ?);", attendance)

        # 10. grades
        grades = [
            (1, 1, 'Midterm Exam', 100, 92.0, 30),
            (2, 1, 'Final Project', 100, 96.0, 40),
            (3, 1, 'Quizzes', 100, 88.0, 30),
            (4, 2, 'Midterm Exam', 100, 89.0, 30),
            (5, 2, 'Final Project', 100, 91.0, 40),
            (6, 2, 'Quizzes', 100, 94.0, 30),
            (7, 3, 'Midterm Exam', 100, 75.0, 30),
            (8, 3, 'Final Project', 100, 80.0, 40),
            (9, 3, 'Quizzes', 100, 78.0, 30)
        ]
        cursor.executemany("INSERT INTO grades VALUES (?, ?, ?, ?, ?, ?);", grades)

        # 11. advising_records
        advising = [
            (1, 1, 1, '2025-10-15', 'Discussed course registration for Spring. Recommended CS201.'),
            (2, 2, 1, '2025-10-18', 'Agreed to pursue honors thesis on Security.'),
            (3, 3, 3, '2025-11-02', 'Reviewed electrical circuit project progress. Satisfactory.')
        ]
        cursor.executemany("INSERT INTO advising_records VALUES (?, ?, ?, ?, ?);", advising)

        # 12. tuition_fees
        fees = [
            (1, 1, 'Fall 2025', 5000.0, 'Tuition'),
            (2, 1, 'Fall 2025', 250.0, 'Lab Fee'),
            (3, 1, 'Spring 2026', 5000.0, 'Tuition'),
            (4, 3, 'Fall 2025', 5500.0, 'Tuition'),
            (5, 2, 'Fall 2025', 7000.0, 'Tuition')
        ]
        cursor.executemany("INSERT INTO tuition_fees VALUES (?, ?, ?, ?, ?);", fees)

        # 13. student_accounts
        accounts = [
            (1, 1, 0.0, 'Paid'),
            (2, 2, 150.0, 'Overdue'),
            (3, 3, 5500.0, 'Unpaid'),
            (4, 4, 1200.0, 'Overdue'),
            (5, 5, 0.0, 'Paid')
        ]
        cursor.executemany("INSERT INTO student_accounts VALUES (?, ?, ?, ?);", accounts)

        # 14. transactions
        transactions = [
            (1, 1, 5250.0, 'Payment', '2025-08-15', 'Credit Card'),
            (2, 2, 5100.0, 'Payment', '2025-08-20', 'Bank Transfer'),
            (3, 4, 5800.0, 'Scholarship Draw', '2025-09-01', 'Internal Transfer')
        ]
        cursor.executemany("INSERT INTO transactions VALUES (?, ?, ?, ?, ?, ?);", transactions)

        # 15. scholarships
        scholarships = [
            (1, 'Merit Scholarship', 50, 'GPA > 3.8'),
            (2, 'Engineering Grant', 20, 'Enrolled in engineering program'),
            (3, 'Need-Based Financial Aid', 100, 'Financial Eligibility')
        ]
        cursor.executemany("INSERT INTO scholarships VALUES (?, ?, ?, ?);", scholarships)

        # 16. student_scholarships
        student_scholarships = [
            (1, 1, '2021-09-01', 'Active'),
            (2, 1, '2020-09-01', 'Active'),
            (3, 2, '2022-09-01', 'Active'),
            (4, 3, '2021-09-01', 'Active')
        ]
        cursor.executemany("INSERT INTO student_scholarships VALUES (?, ?, ?, ?);", student_scholarships)

        # 17. hostels
        hostels = [
            (1, 'Turing Hall', 'North Campus', 'Grace Hopper', 150),
            (2, 'Lovelace Hall', 'South Campus', 'Margaret Hamilton', 100),
            (3, 'Feynman Hall', 'East Campus', 'John von Neumann', 200)
        ]
        cursor.executemany("INSERT INTO hostels VALUES (?, ?, ?, ?, ?);", hostels)

        # 18. hostel_allotments
        allotments = [
            (1, 1, 1, 'A-101', '2021-09-01', None),
            (2, 2, 2, 'B-202', '2020-09-01', None),
            (3, 3, 2, 'B-303', '2022-09-01', None),
            (4, 5, 1, 'A-102', '2023-09-01', None)
        ]
        cursor.executemany("INSERT INTO hostel_allotments VALUES (?, ?, ?, ?, ?, ?);", allotments)

        # 19. library_books
        books = [
            (1, 'Introduction to Algorithms', 'Thomas H. Cormen', '978-0262033848', 'Computer Science', 10, 8),
            (2, 'Computer Networking', 'James F. Kurose', '978-0133594140', 'Computer Science', 5, 4),
            (3, 'University Physics', 'Hugh D. Young', '978-0133969290', 'Physics', 8, 8),
            (4, 'Clean Code', 'Robert C. Martin', '978-0132350884', 'Computer Science', 12, 10),
            (5, 'Calculus', 'James Stewart', '978-1285740621', 'Mathematics', 15, 12)
        ]
        cursor.executemany("INSERT INTO library_books VALUES (?, ?, ?, ?, ?, ?, ?);", books)

        # 20. book_loans
        loans = [
            (1, 1, 1, '2026-05-10', None, 'Borrowed', 0.0),
            (2, 1, 4, '2026-04-01', '2026-04-15', 'Returned', 0.0),
            (3, 2, 2, '2026-05-02', None, 'Borrowed', 5.0),
            (4, 3, 5, '2026-05-15', None, 'Borrowed', 0.0),
            (5, 4, 1, '2026-03-01', None, 'Overdue', 25.0)
        ]
        cursor.executemany("INSERT INTO book_loans VALUES (?, ?, ?, ?, ?, ?, ?);", loans)

        # 21. staff
        staff = [
            (1, 'John', 'Smith', 'john.smith.staff@university.edu', 'IT Support Specialist', 55000.0, '2018-05-10', 1),
            (2, 'Sarah', 'Jones', 'sarah.jones.staff@university.edu', 'Lab Administrator', 48000.0, '2020-02-15', 2),
            (3, 'Emily', 'Davis', 'emily.davis.staff@university.edu', 'Administrative Assistant', 42000.0, '2019-11-01', 4)
        ]
        cursor.executemany("INSERT INTO staff VALUES (?, ?, ?, ?, ?, ?, ?, ?);", staff)

        # 22. assets
        assets = [
            (1, 'Dell PowerEdge Server', 'Server', '2022-06-15', 15000.0, 'Active', 2),
            (2, 'Epson Projector', 'Projector', '2023-01-20', 1200.0, 'Active', 1),
            (3, '3D Printer', 'Lab Equipment', '2024-03-10', 3500.0, 'Maintenance', 2)
        ]
        cursor.executemany("INSERT INTO assets VALUES (?, ?, ?, ?, ?, ?, ?);", assets)

    conn.commit()
    conn.close()
    logger.info("College ERP database initialization completed successfully.")
