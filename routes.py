from flask import render_template, request, redirect, url_for, flash, session, make_response
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from subprocess import Popen, PIPE, run
from forms import StudentSignUpForm, StudentLoginForm, TeacherLoginForm
from models import Student, Teacher, Assignment, Question, Testcase, Submission
from app import app, db, bcrypt
from datetime import datetime
import os
import tempfile

# Configuration for file upload
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'c'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'student_login'  # Redirect to 'login' view if not authenticated

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@login_manager.user_loader
def load_student(student_id):
    return Student.query.get(int(student_id))

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/student_signup', methods=['GET', 'POST'])
def student_signup():
    form = StudentSignUpForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        student = Student(
            name=form.name.data,
            roll=form.roll.data,
            exam_roll=form.exam_roll.data,
            email_id=form.email_id.data,
            password=hashed_password
        )
        db.session.add(student)
        db.session.commit()
        flash('Account created successfully!', 'success')
        return redirect(url_for('index'))
    return render_template('student_signup.html', form=form)


@app.route('/student_login', methods=['GET', 'POST'])
def student_login():
    form = StudentLoginForm()
    if form.validate_on_submit():
        student = Student.query.filter_by(email_id=form.email_id.data).first()
        if student and bcrypt.check_password_hash(student.password, form.password.data):
            login_user(student)
            # Store the student's ID in the session
            session['student_id'] = student.id
            flash('Login successful!', 'success')
            return redirect(url_for('student_dashboard', student_id=student.id))  # Redirect to student dashboard after login
        else:
            flash('Login unsuccessful. Please check email and password.', 'danger')
    return render_template('student_login.html', form=form)


@app.route('/teacher_login', methods=['GET', 'POST'])
def teacher_login():
    form = TeacherLoginForm()
    if form.validate_on_submit():
        teacher = Teacher.query.filter_by(email=form.email.data).first()
        if teacher and bcrypt.check_password_hash(teacher.password, form.password.data):
            flash('Login successful!', 'success')
            session['teacher_id'] = teacher.id
            return redirect(url_for('teacher_dashboard'))  # Redirect to teacher dashboard after login
        else:
            flash('Login unsuccessful. Please check email and password.', 'danger')
    return render_template('teacher_login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    # Check if a student is logged in
    # if 'student_id' in session:
    #     session.pop('student_id', None)  # Remove the student_id from session
    #     flash('You have been logged out as a student.', 'success')
    #
    # # Check if a teacher is logged in
    # elif 'teacher_id' in session:
    #     session.pop('teacher_id', None)  # Remove the teacher_id from session
    #     flash('You have been logged out as a teacher.', 'success')
    # else:
    #     flash('No user is currently logged in.', 'warning')
    logout_user()
    flash('You have been logged out.', 'success')
    # Redirect to login page after logout
    return redirect(url_for('index'))

@app.route('/student_dashboard/<int:student_id>')
@login_required
def student_dashboard(student_id):
    if 'student_id' not in session:
        flash('You must be logged in to submit your work.')
        return redirect(url_for('student_login'))
    elif session['student_id'] != student_id:
        flash('You must be logged in to submit your work.')
        return redirect(url_for('student_login'))
    else:
        student_data = Student.query.filter_by(id=student_id).first()
        group = student_data.group
        # current_date = datetime.today().strftime('%Y-%m-%d')
        current_date = '2024-10-30'
        if group[-1] == '1':
            assignments = Assignment.query.filter(Assignment.date1 <= current_date).all()
        else:
            assignments = Assignment.query.filter(Assignment.date2 <= current_date).all()
        return render_template('student_dashboard.html', assignments=assignments, student_data=student_data)

@app.route('/teacher_dashboard')
def teacher_dashboard():
    if 'teacher_id' not in session:
        flash('You must be logged in to submit your work.')
        return redirect(url_for('teacher_login'))
    # Fetch relevant data (e.g., assignments) if needed
    assignments = Assignment.query.all()  # Or filter based on teacher if needed
    return render_template('teacher_dashboard.html', assignments=assignments)


@app.route('/create_assignment', methods=['GET', 'POST'])
def create_assignment():
    if request.method == 'POST':
        if 'teacher_id' not in session:
            flash('You must be logged in to submit your work.')
            return redirect(url_for('teacher_login'))
        topic = request.form['topic']
        date1 = request.form['date1']
        date2 = request.form['date2']
        due_date1 = request.form['due_date1']
        due_date2 = request.form['due_date2']
        total_marks = request.form['total_marks']
        num_questions = request.form['num_questions']

        # Create an Assignment object
        new_assignment = Assignment(
            topic=topic,
            date1=date1,
            date2=date2,
            due_date1=due_date1,
            due_date2=due_date2,
            total_marks=total_marks,
            num_questions=num_questions
        )

        db.session.add(new_assignment)
        db.session.commit()

        flash('Assignment created successfully!', 'success')
        # Redirect to the add questions page with the new assignment ID
        return redirect(url_for('add_questions', assignment_id=new_assignment.id))

    return render_template('create_assignment.html')

@app.route('/view_assignments', methods=['GET'])
def view_assignments():
    assignments = Assignment.query.all()
    return render_template('view_assignments.html', assignments=assignments)


@app.route('/add_questions/<int:assignment_id>', methods=['GET', 'POST'])
def add_questions(assignment_id):
    if 'teacher_id' not in session:
        flash('You must be logged in to submit your work.')
        return redirect(url_for('teacher_login'))
    assignment = Assignment.query.get_or_404(assignment_id)
    questions = Question.query.filter_by(ass_id=assignment_id).all()
    # Calculate the number of questions and total marks
    total_question_marks = float(sum([question.marks for question in questions]))

    # Check if the number of questions exceeds the allowed limit
    if len(questions) >= assignment.num_questions:
        flash(f'You cannot add more than {assignment.num_questions} questions.', 'danger')
        return redirect(url_for('view_assignment', assignment_id=assignment_id))

    if request.method == 'POST':
        question_text = request.form['question']
        marks = float(request.form['marks'])
        # Check if the total marks exceed the allowed limit
        if total_question_marks + marks > assignment.total_marks:
            flash('The total marks of the questions exceed the assignment\'s allowed total marks.', 'danger')
            return redirect(url_for('view_assignment', assignment_id=assignment_id))

        # Create a Question object
        new_question = Question(
            ass_id=assignment_id,
            question=question_text,
            marks=marks
        )

        db.session.add(new_question)
        db.session.commit()

        flash('Question added successfully!', 'success')
        return redirect(url_for('add_questions', assignment_id=assignment_id))

    return render_template('add_questions.html', assignment=assignment, questions=questions)

@app.route('/add_test_cases/<int:question_id>', methods=['GET', 'POST'])
def add_test_cases(question_id):
    if request.method == 'POST':
        if 'teacher_id' not in session:
            flash('You must be logged in to submit your work.')
            return redirect(url_for('teacher_login'))
        case_input = request.form['case']
        output = request.form['output']

        # Create a Testcase object
        new_testcase = Testcase(
            ques_id=question_id,
            case=case_input,
            output=output
        )

        db.session.add(new_testcase)
        db.session.commit()

        flash('Test case added successfully!', 'success')
        return redirect(url_for('add_test_cases', question_id=question_id))

    question = Question.query.get_or_404(question_id)
    testcases = Testcase.query.filter_by(ques_id=question_id).all()

    return render_template('add_test_cases.html', question=question, testcases=testcases)

@app.route('/delete_testcase/<int:testcase_id>', methods=['POST'])
def delete_testcase(testcase_id):
    if 'teacher_id' not in session:
        flash('You must be logged in to submit your work.')
        return redirect(url_for('teacher_login'))
    testcase = Testcase.query.get_or_404(testcase_id)

    db.session.delete(testcase)
    db.session.commit()

    flash('Test case deleted successfully!', 'success')
    return redirect(url_for('edit_question', question_id=testcase.ques_id))


@app.route('/edit_question/<int:question_id>', methods=['GET', 'POST'])
def edit_question(question_id):
    question = Question.query.get_or_404(question_id)

    if request.method == 'POST':
        if 'teacher_id' not in session:
            flash('You must be logged in to submit your work.')
            return redirect(url_for('teacher_login'))
        # Update question details
        question.question = request.form['question']
        question.marks = request.form['marks']
        db.session.commit()

        # Add a new test case if provided
        new_case = request.form.get('case')
        new_output = request.form.get('output')
        print("New case:", new_case)
        print("New output:", new_output)
        if new_case and new_output:
            new_testcase = Testcase(
                ques_id=question.id,
                case=new_case,
                output=new_output
            )
            db.session.add(new_testcase)
            db.session.commit()
            flash('New test case added!', 'success')

        flash('Question updated successfully!', 'success')
        return redirect(url_for('edit_question', question_id=question_id))

    # Retrieve all existing test cases for the question
    testcases = Testcase.query.filter_by(ques_id=question_id).all()

    return render_template('edit_question.html', question=question, testcases=testcases)


@app.route('/edit_testcase/<int:testcase_id>', methods=['GET', 'POST'])
def edit_testcase(testcase_id):
    testcase = Testcase.query.get_or_404(testcase_id)

    if request.method == 'POST':
        if 'teacher_id' not in session:
            flash('You must be logged in to submit your work.')
            return redirect(url_for('teacher_login'))
        testcase.case = request.form['case']
        testcase.output = request.form['output']

        db.session.commit()
        flash('Test case updated successfully!', 'success')
        return redirect(url_for('view_assignment', assignment_id=testcase.question.ass_id))

    return render_template('edit_testcase.html', testcase=testcase)


@app.route('/view_assignment/<int:assignment_id>', methods=['GET'])
def view_assignment(assignment_id):
    assignment = Assignment.query.get_or_404(assignment_id)
    questions = Question.query.filter_by(ass_id=assignment_id).all()

    question_details = []
    total_question_marks = 0
    for question in questions:
        testcases = Testcase.query.filter_by(ques_id=question.id).all()
        question_details.append({
            'question': question,
            'testcases': testcases
        })
    return render_template('view_assignment.html',
                           assignment=assignment,
                           student_id=None,
                           question_details=question_details,
                           submission_details=None)

@app.route('/view_assignment_student/<int:assignment_id>', methods=['GET'])
@login_required
def view_assignment_student(assignment_id):
    if 'student_id' not in session:
        flash('You must be logged in to submit your work.')
        return redirect(url_for('student_login'))

    current_student_id = session['student_id']
    assignment = Assignment.query.get_or_404(assignment_id)
    questions = Question.query.filter_by(ass_id=assignment_id).all()

    question_details = []
    submission_details = {}
    for question in questions:
        testcases = Testcase.query.filter_by(ques_id=question.id).all()
        testcase_submissions = {}
        for testcase in testcases:
            submission = Submission.query.filter_by(st_id=current_student_id, ques_id=question.id,
                                                    test_case_id=testcase.id).first()
            if submission:
                testcase_submissions[testcase.id] = submission.output
            else:
                testcase_submissions[testcase.id] = None  # No submission found for this test case

        question_details.append({
            'question': question,
            'testcases': testcases,
            'testcase_submissions': testcase_submissions  # Storing test case outputs
        })

    return render_template('view_assignment_student.html',
                           assignment=assignment,
                           question_details=question_details,
                           student_id=current_student_id)

@app.route('/delete_assignment/<int:assignment_id>', methods=['POST'])
def delete_assignment(assignment_id):
    assignment = Assignment.query.get_or_404(assignment_id)

    # Delete the assignment and its associated questions and test cases
    db.session.delete(assignment)
    db.session.commit()

    flash('Assignment deleted successfully!', 'success')
    return redirect(url_for('view_assignments'))

@app.route('/edit_assignment/<int:assignment_id>', methods=['GET', 'POST'])
def edit_assignment(assignment_id):
    assignment = Assignment.query.get_or_404(assignment_id)

    if request.method == 'POST':
        # Get the updated data from the form
        assignment.topic = request.form['topic']
        assignment.total_marks = float(request.form['total_marks'])
        assignment.date1 = request.form['date1']
        assignment.date2 = request.form['date2']
        assignment.due_date1 = request.form['due_date1']
        assignment.due_date2 = request.form['due_date2']
        assignment.num_questions = int(request.form['num_questions'])

        # Save the updated assignment to the database
        db.session.commit()
        flash('Assignment updated successfully!', 'success')
        return redirect(url_for('view_assignment', assignment_id=assignment.id))

    return render_template('edit_assignment.html', assignment=assignment)


@app.route('/upload_submission/<int:question_id>/<int:assignment_id>', methods=['POST'])
@login_required
def upload_submission(question_id, assignment_id):
    if 'student_id' not in session:
        flash('You must be logged in to submit your work.')
        return redirect(url_for('login'))

    current_student_id = session['student_id']
    if 'file' not in request.files:
        flash('No file part')
        return redirect(url_for('view_assignment_student', assignment_id=assignment_id))

    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        return redirect(url_for('view_assignment_student', assignment_id=assignment_id))

    if file and allowed_file(file.filename):
        filename = secure_filename(f"{assignment_id}_{current_student_id}_{question_id}.c")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Run the .c file evaluation (this is an example, adjust it to your system)
        compile_process = Popen(['gcc', filepath, '-o', filepath + '.out'], stdout=PIPE, stderr=PIPE)
        compile_output, compile_errors = compile_process.communicate()

        if compile_process.returncode != 0:
            flash(f"Compilation error: {compile_errors.decode('utf-8')}", "error")
            return redirect(url_for('view_assignment_student', assignment_id=assignment_id))
        else:
            print("Compile output:", compile_output)

        # Now, run the compiled program with test cases
        test_cases = Testcase.query.filter_by(ques_id=question_id).all()
        question_data = Question.query.filter_by(id=question_id).first()
        test_cases_passed = 0
        for idx, test_case_row in enumerate(test_cases):
            print(f"TEST CASE {idx+1}:")
            test_case = test_case_row.case
            if '<>' in test_case:   # No input required
                print("Running program:", filepath + '.out')
                run_process = run([filepath + '.out'], capture_output=True)
                output = run_process.stdout
                errors = run_process.stderr
            elif ';' in test_case:
                test_case = '\n'.join(test_case.split(';'))
                print("Running program:", filepath + '.out', '<', test_case)
                run_process = run([filepath + '.out'], capture_output=True, text=True,
                                  input=test_case, encoding='utf-8')
                output = run_process.stdout
                errors = run_process.stderr
            else:
                print("Running program:", filepath + '.out', '<', test_case)
                run_process = run([filepath + '.out'], capture_output=True, text=True,
                                  input=test_case, encoding='utf-8')
                output = run_process.stdout
                errors = run_process.stderr

            desired_output = test_case_row.output
            if run_process.returncode != 0:
                flash(f"Runtime error: {errors.decode('utf-8')}", "error")
                return redirect(url_for('view_assignment_student', assignment_id=assignment_id))
            else:
                output = output.decode('utf-8')
                print("Run output:", output)
                if desired_output == '<>':
                    marks = float(question_data.marks)/len(test_cases)
                    # test_cases_passed = -1
                elif ';' in desired_output:
                    desired_output = '\n'.join(desired_output.split(';'))
                    if output == desired_output:
                        # test_cases_passed += 1
                        marks = float(question_data.marks)/len(test_cases)
                    else:
                        print(f"Code Output - Desired Output Mismatch\nCode output:\t{output}\nDesired output:\t{desired_output}")
                        marks = 0.0
                else:
                    if output == desired_output:
                        # test_cases_passed += 1
                        marks = float(question_data.marks)/len(test_cases)
                    else:
                        print(
                            f"Code Output - Desired Output Mismatch\nCode output:\t{output}\nDesired output:\t{desired_output}")
                        marks = 0.0
                test_case_id = test_case_row.id

                # Save the marks to the database
                current_date = datetime.today()
                submission = Submission(st_id=current_student_id, date=current_date,
                                        ass_id=assignment_id, ques_id=question_id, marks=marks,
                                        test_case_id=test_case_id, output=output)
                db.session.add(submission)
                db.session.commit()

                flash(f"File uploaded and evaluated. You received {marks} marks.")
        return redirect(url_for('view_assignment_student',
                                assignment_id=assignment_id))

    flash('Invalid file format. Only .c files are allowed.', 'error')
    return redirect(url_for('view_assignment_student', assignment_id=assignment_id))