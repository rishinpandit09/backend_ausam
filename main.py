from datetime import datetime

from flask import Flask, render_template, request, url_for, redirect, jsonify, render_template
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow

app = Flask(__name__)
# SQL ALCHEMY


app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db.sqlite3"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
ma = Marshmallow(app)


class Person(db.Model):
    person_id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    gate_id = db.Column(db.String(100))
    reason = db.Column(db.String(500))
    request_time = db.Column(db.DateTime)
    entry_given = db.Column(db.Boolean)
    entry_given_time = db.Column(db.DateTime)

    def __int__(self, first_name, last_name, email, gate_id, reason, request_time, entry_given, entry_given_time):
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.gate_id = gate_id
        self.reason = reason
        self.request_time = request_time
        self.entry_given = entry_given
        self.entry_given_time = entry_given_time


class PersonSchema(ma.Schema):
    class Meta:
        fields = ('id', 'first_name', 'last_name', 'email', 'gate_id', 'reason', 'request_time', 'entry_given',
                  'entry_given_time')


class Controller(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    designation = db.Column(db.String(500))

    def __int__(self, first_name, last_name, email, designation):
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.designation = designation


class ControllerSchema(ma.Schema):
    class Meta:
        fields = ('id', 'first_name', 'last_name', 'email', 'designation')


class Gate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    gate_name = db.Column(db.String(100))

    def __int__(self, gate_name):
        self.gate_name = gate_name


class GateSchema(ma.Schema):
    class Meta:
        fields = ('id', 'gate_name')


class GateAccess(db.Model):
    gate_access_id = db.Column(db.Integer, primary_key=True)
    controller_id = db.Column(db.Integer)
    gate_id = db.Column(db.Integer)

    def __int__(self, controller_id, gate_id):
        self.controller_id = controller_id
        self.gate_id = gate_id


class GateAccessSchema(ma.Schema):
    class Meta:
        fields = ('controller_id', 'gate_id')


# Initialize schema
person_schema = PersonSchema()
persons_schema = PersonSchema(many=True)
controller_schema = ControllerSchema()
controllers_schema = ControllerSchema(many=True)
gate_schema = GateSchema()
gates_schema = GateSchema(many=True)
gate_access_schema = GateAccessSchema()
gates_access_schema = GateAccessSchema(many=True)
app.app_context().push()
db.create_all()


# Endpoints
@app.route('/', methods=["GET", "POST"])
def saveDetails():
    message = "message"
    if request.method == "POST":
        try:
            first_name = request.form["first_name"]
            last_name = request.form["last_name"]
            email = request.form["email"]
            gate_id = request.form['gate_id']
            reason = request.form['reason']
            request_time = datetime.now()
            entry_given = False
            entry_given_time = datetime.now()
            new_person_request = Person(first_name, last_name, email, gate_id, reason, request_time, entry_given,
                                        entry_given_time)
            db.session.add(new_person_request)
            db.session.commit()

            msg = "Successfully"

        except:
            db.session.rollback()
            msg = "We cannot add the person to the list"

        finally:
            print(msg)
            return render_template("thankyou.html")
    return render_template("index.html")


@app.route('/thankyou')
def thankyou_page():
    return render_template('thankyou.html')


#
if __name__ == '__main__':
    app.run(debug=True)
