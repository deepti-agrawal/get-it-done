from flask import Flask, request, redirect, render_template, session, flash
from flask_sqlalchemy import SQLAlchemy
import cgi
from hashutils import make_pw_hash, check_pw_hash

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://get-it-done:Productive@localhost:8889/get-it-done'
app.config['SQLALCHEMY_ECHO'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = '123ndh78'
db = SQLAlchemy(app) #Constructor db object to use in application

class Task(db.Model):
    id = db.Column(db.Integer,primary_key = True)
    name = db.Column(db.String(120))
    completed = db.Column(db.Boolean)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __init__(self,name, owner):
        self.name = name
        self.completed = False
        self.owner = owner

class User(db.Model):
   id = db.Column(db.Integer,primary_key = True)
   email = db.Column(db.String(120), unique = True)
   pw_hash = db.Column(db.String(120))
   tasks = db.relationship('Task', backref='owner')

   def __init__(self,email,password):
       self.email = email
       self.pw_hash = make_pw_hash(password)

@app.before_request
def require_login():
    allowed_routes = ['login','register']
    if request.endpoint not in allowed_routes and 'email' not in session:
        return redirect("/login")


@app.route('/login',methods = ['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email = email).first()
        if user and check_pw_hash(password,user.pw_hash):
            session['email'] = email
            flash("Logged in...")
            return redirect('/')
        else:
            flash("Invalid username or password...",'error')
    return render_template('login.html')

@app.route('/register',methods = ['GET','POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        verify = request.form['verify']
        #TODO validate user data
        existing_user = User.query.filter_by(email = email).first()
        if not existing_user:
            new_user = User(email,password)
            db.session.add(new_user)
            db.session.commit()
            session['email'] = email
            return redirect("/")
        else:
            #TODO better response
            return '<h1>Duplicate User</h1>'
    return render_template('register.html')

@app.route('/',methods = ['POST','GET'])
def index():
    owner = User.query.filter_by(email=session['email']).first()
    if request.method == 'POST':
        task_name = request.form['task']        
        new_task = Task(task_name, owner)
        db.session.add(new_task)
        db.session.commit()

    tasks =  Task.query.filter_by(completed=False,owner = owner).all()
    completed_tasks =  Task.query.filter_by(completed=True, owner = owner).all()
    return render_template('todos.html',title="Get it Done!",tasks=tasks,completed_tasks=completed_tasks)

@app.route('/delete-task',methods = ['POST'])
def delete_task():
    task_id = int(request.form['task-id'])
    task = Task.query.get(task_id)
    task.completed = True
    db.session.add(task)
    db.session.commit()
    return redirect("/")

@app.route('/logout')
def logout():
    del session['email']
    return redirect("/login")

if __name__ == '__main__':
    app.run()