from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
db = SQLAlchemy()

class Student(UserMixin, db.Model):
    __tablename__ = 'student'  # Changed to lowercase for PostgreSQL convention
    id = db.Column(db.Integer, primary_key=True)
    roll = db.Column(db.String(10), unique=True, nullable=False)
    exam_roll = db.Column(db.String(10), nullable=True)
    name = db.Column(db.String(100), nullable=False)
    group = db.Column(db.String(2))
    email_id = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    lab_marks = db.Column(db.Numeric(5, 2))  # Changed back to Numeric for PostgreSQL
    attendance_marks = db.Column(db.Numeric(5, 2))
    viva_marks = db.Column(db.Numeric(5, 2))
    report_marks = db.Column(db.Numeric(5, 2))

    def __repr__(self):
        return f"<Student {self.name}>"

class Teacher(db.Model):
    __tablename__ = 'teacher'  # Changed to lowercase for PostgreSQL convention
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return f"<Teacher {self.name}>"


class Assignment(db.Model):
    __tablename__ = 'assignment'  # Changed to lowercase for PostgreSQL convention
    id = db.Column(db.Integer, primary_key=True)
    date1 = db.Column(db.Date)
    date2 = db.Column(db.Date)
    due_date1 = db.Column(db.Date)
    due_date2 = db.Column(db.Date)
    topic = db.Column(db.String(255), nullable=False)
    total_marks = db.Column(db.Numeric(5, 2))  # Changed back to Numeric for PostgreSQL
    num_questions = db.Column(db.Integer)
    questions = db.relationship('Question', backref='assignment', cascade="all, delete", lazy=True)
    
    def __repr__(self):
        return f"<Assignment {self.topic}>"  # Changed from self.name to self.topic


class Question(db.Model):
    __tablename__ = 'question'  # Changed to lowercase for PostgreSQL convention
    id = db.Column(db.Integer, primary_key=True)
    ass_id = db.Column(db.Integer, db.ForeignKey('assignment.id'))  # Updated foreign key reference
    question = db.Column(db.Text, nullable=False)
    marks = db.Column(db.Numeric(5, 2))  # Changed back to Numeric for PostgreSQL
    optional = db.Column(db.Boolean, default=False)
    testcases = db.relationship('Testcase', backref='question', cascade="all, delete", lazy=True)
    
    def __repr__(self):
        return f"<Question {self.id}>"  # Changed from self.name to self.id

class Testcase(db.Model):
    __tablename__ = 'testcase'  # Changed to lowercase for PostgreSQL convention
    id = db.Column(db.Integer, primary_key=True)
    ques_id = db.Column(db.Integer, db.ForeignKey('question.id'))  # Updated foreign key reference
    case = db.Column(db.Text, nullable=False)
    output = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return f"<Testcase {self.id}>"  # Changed from self.name to self.id


class Submission(db.Model):
    __tablename__ = 'submission'  # Changed to lowercase for PostgreSQL convention
    id = db.Column(db.Integer, primary_key=True)
    st_id = db.Column(db.Integer, db.ForeignKey('student.id'))  # Updated foreign key reference
    date = db.Column(db.Date)
    ass_id = db.Column(db.Integer, db.ForeignKey('assignment.id'))  # Updated foreign key reference
    ques_id = db.Column(db.Integer, db.ForeignKey('question.id'))  # Updated foreign key reference
    test_case_id = db.Column(db.Integer, db.ForeignKey('testcase.id'))  # Updated foreign key reference
    output = db.Column(db.String(1000))
    num_test_cases_passed = db.Column(db.Integer)
    marks = db.Column(db.Numeric(5, 2))  # Changed back to Numeric for PostgreSQL
    feedback = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f"<Submission {self.id}>"  # Changed from self.name to self.id