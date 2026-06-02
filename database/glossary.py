# Upgraded Business Glossary & Column Descriptions with SQL Few-Shot Prompting (No SELECT * Wildcards)

BUSINESS_GLOSSARY = {
    "departments": (
        "Academic divisions (e.g., Computer Science, Mathematics). "
        "Fields: dept_name, budget (division funding), head_id (instructor leading the dept). "
        "Sample Query: 'What is the budget of CS?' "
        "SQL: SELECT budget FROM departments WHERE code = 'CS';"
    ),
    "programs": (
        "Degree plans of study (e.g., BS Computer Science, MS Cybersecurity). "
        "Fields: program_name, duration_years, total_credits. "
        "Links: connects to departments via dept_id. "
        "Sample Query: 'How many credits are required for BS Computer Science?' "
        "SQL: SELECT total_credits FROM programs WHERE program_name = 'BS Computer Science';"
    ),
    "students": (
        "Profiles of enrolled students. "
        "Fields: first_name, last_name, email, enrollment_date, status (Active, Suspended, Graduated). "
        "Links: belongs to programs via program_id. "
        "Sample Query: 'Find all active students' "
        "SQL: SELECT student_id, first_name, last_name, email FROM students WHERE status = 'Active';"
    ),
    "instructors": (
        "Faculty profiles and advising assignments. "
        "Fields: first_name, last_name, email, hire_date, status (Active, On Leave). "
        "Links: reports to departments via dept_id. "
        "Sample Query: 'List active instructors in CS' "
        "SQL: SELECT i.instructor_id, i.first_name, i.last_name FROM instructors i JOIN departments d ON i.dept_id = d.dept_id WHERE i.status = 'Active' AND d.code = 'CS';"
    ),
    "courses": (
        "Academic course catalogs and syllabus credit weights. "
        "Fields: course_title, course_code (e.g., CS101), credits. "
        "Links: offered by departments via dept_id. "
        "Sample Query: 'List courses offered by Mathematics' "
        "SQL: SELECT c.course_title FROM courses c JOIN departments d ON c.dept_id = d.dept_id WHERE d.code = 'MA';"
    ),
    "classrooms": (
        "Campus physical assets and room specs. "
        "Fields: room_number, building, capacity, room_type (Lecture Hall, Lab, Auditorium). "
        "Sample Query: 'Find labs with capacity over 30' "
        "SQL: SELECT classroom_id, room_number, building FROM classrooms WHERE room_type = 'Lab' AND capacity > 30;"
    ),
    "sections": (
        "Class schedule instances connecting courses to instructors and classrooms. "
        "Fields: semester (Fall, Spring), academic_year, schedule_pattern (MWF 09:00-10:00). "
        "Links: joins courses, instructors, and classrooms. "
        "Sample Query: 'What room is EE101 scheduled in?' "
        "SQL: SELECT cl.room_number FROM sections s JOIN courses c ON s.course_id = c.course_id JOIN classrooms cl ON s.classroom_id = cl.classroom_id WHERE c.course_code = 'EE101';"
    ),
    "enrollments": (
        "Class registration mappings linking students to sections. "
        "Fields: enrollment_date, status (Completed, Active), grade_points (GPA scale 0.0 - 4.0). "
        "Links: joins students and sections. "
        "Sample Query: 'Find GPA of student 1' "
        "SQL: SELECT grade_points FROM enrollments WHERE student_id = 1;"
    ),
    "attendance": (
        "Classroom daily attendance logger. "
        "Fields: class_date, status (Present, Absent). "
        "Links: references enrollments via enrollment_id. "
        "Sample Query: 'List absences for student 1 in CS101' "
        "SQL: SELECT a.class_date FROM attendance a JOIN enrollments e ON a.enrollment_id = e.enrollment_id JOIN sections s ON e.section_id = s.section_id JOIN courses c ON s.course_id = c.course_id WHERE e.student_id = 1 AND c.course_code = 'CS101' AND a.status = 'Absent';"
    ),
    "grades": (
        "Individual grading components and score metrics. "
        "Fields: assessment_name (Midterm Exam, Final Project, Quizzes), max_marks, marks_obtained, weightage_percent. "
        "Links: references enrollments via enrollment_id. "
        "Sample Query: 'Find midterm exam mark for student 1' "
        "SQL: SELECT marks_obtained FROM grades g JOIN enrollments e ON g.enrollment_id = e.enrollment_id WHERE e.student_id = 1 AND g.assessment_name = 'Midterm Exam';"
    ),
    "advising_records": (
        "Academic counseling notes between students and advisors. "
        "Fields: advising_date, notes (advising details). "
        "Links: joins students and instructors. "
        "Sample Query: 'Who advised Jane Smith?' "
        "SQL: SELECT i.last_name FROM advising_records ar JOIN students s ON ar.student_id = s.student_id JOIN instructors i ON ar.instructor_id = i.instructor_id WHERE s.first_name = 'Jane' AND s.last_name = 'Smith';"
    ),
    "tuition_fees": (
        "Fee billing structures mapped to degree plans. "
        "Fields: semester, amount (tuition rate charged), billing_category (Tuition, Lab Fee). "
        "Links: maps to programs via program_id. "
        "Sample Query: 'What is the tuition amount for MS Cybersecurity?' "
        "SQL: SELECT amount FROM tuition_fees f JOIN programs p ON f.program_id = p.program_id WHERE p.program_name = 'MS Cybersecurity';"
    ),
    "student_accounts": (
        "Financial ledger of student account balances. "
        "Fields: balance (outstanding unpaid tuition fees), status (Paid, Overdue, Unpaid). "
        "Links: belongs to students via student_id. "
        "Sample Query: 'Show total unpaid fees outstanding' "
        "SQL: SELECT SUM(balance) FROM student_accounts WHERE status = 'Unpaid';"
    ),
    "transactions": (
        "Student payment transactions history. "
        "Fields: amount, transaction_type (Payment, Scholarship Draw), transaction_date, payment_method (Credit Card, Bank Transfer). "
        "Links: points to student_accounts via account_id. "
        "Sample Query: 'Find credit card payments' "
        "SQL: SELECT transaction_id, amount, transaction_date FROM transactions WHERE payment_method = 'Credit Card';"
    ),
    "scholarships": (
        "Available tuition grants and eligibility rules. "
        "Fields: name, amount_percent (tuition discount rate), criteria (eligibility requirements, e.g. GPA > 3.8). "
        "Sample Query: 'Show criteria for Merit Scholarship' "
        "SQL: SELECT criteria FROM scholarships WHERE name = 'Merit Scholarship';"
    ),
    "student_scholarships": (
        "Active student scholarship allotments. "
        "Fields: awarded_date, status (Active, Expired). "
        "Links: joins students and scholarships. "
        "Sample Query: 'Find scholarships awarded to student 1' "
        "SQL: SELECT s.name FROM student_scholarships ss JOIN scholarships s ON ss.scholarship_id = s.scholarship_id WHERE ss.student_id = 1;"
    ),
    "hostels": (
        "Campus dormitories information. "
        "Fields: hostel_name (Turing Hall, Lovelace Hall), address, warden_name, total_rooms. "
        "Sample Query: 'Who is the warden of Turing Hall?' "
        "SQL: SELECT warden_name FROM hostels WHERE hostel_name = 'Turing Hall';"
    ),
    "hostel_allotments": (
        "Student dorm occupancy log. "
        "Fields: room_number (dorm room number), allotment_date, check_out_date. "
        "Links: joins students and hostels. "
        "Sample Query: 'Which room in Turing Hall is student 1 assigned to?' "
        "SQL: SELECT room_number FROM hostel_allotments WHERE student_id = 1 AND check_out_date IS NULL;"
    ),
    "library_books": (
        "Library books catalogs. "
        "Fields: title, author, isbn, category (Computer Science, Mathematics, Physics), total_copies, available_copies. "
        "Sample Query: 'Find available copies of Clean Code' "
        "SQL: SELECT available_copies FROM library_books WHERE title = 'Clean Code';"
    ),
    "book_loans": (
        "Library checkouts tracker. "
        "Fields: checkout_date, return_date, status (Borrowed, Returned, Overdue), fine_amount (penalty fees). "
        "Links: joins students and library_books. "
        "Sample Query: 'List outstanding fines on book loans' "
        "SQL: SELECT SUM(fine_amount) FROM book_loans WHERE status = 'Overdue';"
    ),
    "staff": (
        "Non-academic support personnel profiles and payroll. "
        "Fields: first_name, last_name, email, job_title (IT Support, Lab Administrator), salary, hire_date. "
        "Links: reports to departments via dept_id. "
        "Sample Query: 'Show salaries of IT support specialists' "
        "SQL: SELECT salary FROM staff WHERE job_title = 'IT Support Specialist';"
    ),
    "assets": (
        "Institutional hardware properties inventory. "
        "Fields: asset_name (Dell Server, Projector), asset_type, purchase_date, purchase_cost (purchase price), status (Active, Maintenance). "
        "Links: located in classrooms via location_classroom_id. "
        "Sample Query: 'What was the purchase cost of the Dell Server?' "
        "SQL: SELECT purchase_cost FROM assets WHERE asset_name = 'Dell PowerEdge Server';"
    )
}

SEMANTIC_COLUMN_DESCRIPTIONS = {
    "student_accounts.balance": "outstanding financial obligations / unpaid student fees",
    "student_accounts.status": "tuition payment standing status (e.g. Paid, Overdue, Unpaid)",
    "enrollments.grade_points": "grade point average weight (GPA on a 4.0 scale)",
    "book_loans.fine_amount": "library penalty fees / overdue book return fines",
    "departments.budget": "academic division funding budget",
    "grades.marks_obtained": "marks scored in assessment",
    "grades.max_marks": "maximum possible marks for assessment",
    "grades.weightage_percent": "influence rate of assessment on overall grade",
    "hostel_allotments.room_number": "dorm room number allocation",
    "tuition_fees.amount": "charged tuition and fee rates",
    "scholarships.amount_percent": "discount rate applied to tuition",
    "assets.purchase_cost": "property asset value / hardware equipment cost",
    "students.enrollment_date": "The date when the student first enrolled/admitted to the university",
    "students.status": "The general university enrollment status of the student (Active, Suspended, Graduated)",
    "enrollments.enrollment_date": "The date when the student registered/enrolled in a specific course section class",
    "enrollments.status": "The registration status of a student in a specific course section class (Completed, Active)"
}
