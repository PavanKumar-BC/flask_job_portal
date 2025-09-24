from flask import Flask, render_template, request, redirect, url_for, session, flash
from models import db, User, Job, Application
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "8660346631"

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///jobportal_clean.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# ========================
# Home route
# ========================
@app.route('/')
def home():
    return redirect(url_for('login'))

# ========================
# Registration
# ========================
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        role = request.form.get('role', 'candidate')

        if User.query.filter_by(email=email).first():
            flash("Email already registered!", "error")
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(username=username, email=email, password=hashed_password, role=role)
        db.session.add(new_user)
        db.session.commit()

        flash("Registration successful! Please login.", "success")
        return redirect(url_for('login'))

    return render_template('register.html')

# ========================
# Login
# ========================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()
        if not user or not check_password_hash(user.password, password):
            flash("Invalid email or password!", "error")
            return redirect(url_for('login'))

        session['user_id'] = user.id
        session['username'] = user.username
        session['role'] = user.role

        flash(f"Welcome, {user.username}!", "success")

        # Redirect based on role
        if user.role == "recruiter":
            return redirect(url_for('recruiter_dashboard'))
        else:
            return redirect(url_for('candidate_dashboard'))

    return render_template('login.html')

# ========================
# Logout
# ========================
@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully!", "success")
    return redirect(url_for('login'))

# ========================
# Candidate Dashboard
# ========================
@app.route('/candidate-dashboard')
def candidate_dashboard():
    if 'user_id' not in session or session.get('role') != 'candidate':
        flash("Access denied!", "error")
        return redirect(url_for('login'))

    jobs = Job.query.all()
    return render_template('candidate_dashboard.html', jobs=jobs)

# ========================
# Recruiter Dashboard
# ========================
@app.route('/recruiter-dashboard')
def recruiter_dashboard():
    if 'user_id' not in session or session.get('role') != 'recruiter':
        flash("Access denied!", "error")
        return redirect(url_for('login'))

    jobs_posted = Job.query.filter_by(recruiter_id=session['user_id']).all()
    return render_template('recruiter_dashboard.html', jobs=jobs_posted)

# ========================
# Post Job (Recruiter)
# ========================
@app.route('/post-job', methods=['GET', 'POST'])
def post_job():
    if 'user_id' not in session or session.get('role') != 'recruiter':
        flash("Access denied!", "error")
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form['title']
        company = request.form['company']
        location = request.form['location']
        salary = request.form.get('salary', '')
        description = request.form['description']

        job = Job(
            title=title,
            company=company,
            location=location,
            salary=salary,
            description=description,
            recruiter_id=session['user_id']
        )
        db.session.add(job)
        db.session.commit()

        flash("Job posted successfully!", "success")
        return redirect(url_for('recruiter_dashboard'))

    return render_template('post_job.html')

# ========================
# Apply Job (Candidate)
# ========================
@app.route('/apply-job/<int:job_id>', methods=['GET', 'POST'])
def apply_job(job_id):
    if 'user_id' not in session or session.get('role') != 'candidate':
        flash("Access denied!", "error")
        return redirect(url_for('login'))

    job = Job.query.get_or_404(job_id)

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        cover_letter = request.form.get('cover_letter', '')

        # Save application
        application = Application(
            candidate_id=session['user_id'],
            job_id=job.id,
            name=name,
            email=email,
            cover_letter=cover_letter
        )
        db.session.add(application)
        db.session.commit()

        flash(f"You have applied for {job.title}!", "success")
        return redirect(url_for('candidate_dashboard'))

    return render_template('apply_job.html', job=job)

# ========================
# View Applicants (Recruiter)
# ========================
@app.route('/view-applicants/<int:job_id>')
def view_applicants(job_id):
    if 'user_id' not in session or session.get('role') != 'recruiter':
        flash("Access denied!", "error")
        return redirect(url_for('login'))

    job = Job.query.get_or_404(job_id)
    if job.recruiter_id != session['user_id']:
        flash("You can only view applicants for your jobs.", "error")
        return redirect(url_for('recruiter_dashboard'))

    applications = job.applications
    return render_template('view_applicants.html', job=job, applications=applications)

# ========================
# Run App
# ========================
if __name__ == "__main__":
    with app.app_context():
        db.drop_all()  # drop old tables to avoid schema issues
        db.create_all()  # create fresh tables
    app.run(debug=True)

