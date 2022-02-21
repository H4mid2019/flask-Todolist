from flask import Flask, jsonify, render_template , request, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime
import os
import uuid
import string
import random
from logging import FileHandler, WARNING


app = Flask(__name__)
db_path = os.path.join(os.path.dirname(__file__), 'sqlite3.db')

file_handler = FileHandler("logs.txt")
file_handler.setLevel(WARNING)
app.logger.addHandler(file_handler)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///{}'.format(db_path)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = uuid.uuid4().hex

db = SQLAlchemy(app)
migrate = Migrate(app, db)

def random_string(x=random.randrange(16, 32, 1)):
    return ''.join(random.choice([*string.ascii_lowercase, *string.ascii_uppercase]) for _ in range(x))

class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    date_created = db.Column(db.DateTime,default=datetime.utcnow)
    user_id = db.Column(db.String(200), nullable=False)

    def __repr__(self):
        return '<Task %r>' % self.id

 

@app.route('/', methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        task_content = request.form['content']
        old_user = session.get('user_id')
        user_id = old_user if bool(old_user) else random_string(32)
        new_task = Todo(content=task_content, user_id=user_id)
        try:
            db.session.add(new_task)
            db.session.commit()
            if not bool(old_user):
                session['user_id'] = user_id
            return jsonify({"success":"added", "content": request.form['content']}), 201
        except Exception as e:
            print(str(e))
            return jsonify({"error":"couldn't added.", "content": request.form['content']}), 403

    tasks = Todo.query.filter_by(user_id=session.get('user_id')).order_by(Todo.date_created).all()
    return render_template('index.html',tasks=tasks)

@app.route('/delete/<int:id>', methods=['DELETE'])
def delete(id):
    task = Todo.query.filter_by(user_id=session.get('user_id')).all()
    if bool(task):
        task_to_delete = Todo.query.get_or_404(id)

        try:
            db.session.delete(task_to_delete)
            db.session.commit()
            return jsonify({"success":"deleted"}), 204
        except:
            return 'An error occured'
    return jsonify({"error":"This task doesn't belong to you"}), 400


@app.route('/update/<int:id>', methods=['PUT'])
def update(id):
    task = Todo.query.get_or_404(id)

    if request.method == 'PUT':
        task = Todo.query.filter_by(user_id=session.get('user_id')).all()[0]
        if bool(task):
            task.content = request.form['content']

            try:
                db.session.commit()
                return jsonify({"success":"updated", 'content': request.form['content']}), 201

            except:
                return 'An error occured'

    return jsonify({"error":"This task doesn't belong to you"}), 400



if __name__ == "__main__":
    app.run(debug=True)