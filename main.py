from flask import (
    Flask,
    render_template,
    request,
    url_for,
    redirect,
    jsonify,
    render_template,
)
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_httpauth import HTTPTokenAuth
from flask_cors import CORS
from datetime import datetime
from hashlib import sha256
import random
import string

app = Flask(__name__)
CORS(app)
auth = HTTPTokenAuth(scheme="Bearer", realm=None, header="Authentication")


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

    def __init__(
        self,
        first_name,
        last_name,
        email,
        gate_id,
        reason,
        request_time,
        entry_given,
        entry_given_time,
    ):
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
        fields = (
            "id",
            "first_name",
            "last_name",
            "email",
            "gate_id",
            "reason",
            "request_time",
            "entry_given",
            "entry_given_time",
        )


class ControllerApproval(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    controller_id = db.Column(db.Integer)
    person_id = db.Column(db.Integer)
    approval = db.Column(db.Boolean)
    approval_time = db.Column(db.DateTime, default=datetime.now)

    def __init__(self, controller_id, person_id, approval):
        self.controller_id = controller_id
        self.person_id = person_id
        self.approval = approval


class ControllerApprovalSchema(ma.Schema):
    class Meta:
        fields = ("id", "controller_id", "person_id", "approval", "approval_time")


class Controller(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    designation = db.Column(db.String(500))
    password_hash = db.Column(db.String(300))

    def __init__(self, first_name, last_name, email, designation, password_hash):
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.designation = designation
        self.password_hash = password_hash


class ControllerSchema(ma.Schema):
    class Meta:
        fields = ("id", "first_name", "last_name", "email", "designation")


class Gate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    gate_name = db.Column(db.String(100))

    def __init__(self, gate_name):
        self.gate_name = gate_name


class GateSchema(ma.Schema):
    class Meta:
        fields = ("id", "gate_name")


class GateAccess(db.Model):
    gate_access_id = db.Column(db.Integer, primary_key=True)
    controller_id = db.Column(db.Integer)
    gate_id = db.Column(db.Integer)

    def __init__(self, controller_id, gate_id):
        self.controller_id = controller_id
        self.gate_id = gate_id


class GateAccessSchema(ma.Schema):
    class Meta:
        fields = ("controller_id", "gate_id")


class Session(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(100))
    controller_id = db.Column(db.Integer)
    session_start_time = db.Column(db.DateTime, default=datetime.now)

    def __init__(self, session_id, controller_id):
        self.session_id = session_id
        self.controller_id = controller_id


class SessionSchema(ma.Schema):
    class Meta:
        fields = ("id", "session_id", "controller_id", "session_start_time")


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
@app.route("/", methods=["GET", "POST"])
def saveDetails():
    msg = ""
    if request.method == "POST":
        try:
            first_name = request.form["first_name"]
            last_name = request.form["last_name"]
            email = request.form["email"]
            gate_id = int(request.form["gate_id"])
            reason = request.form["reason"]
            request_time = datetime.now()
            entry_given = False
            entry_given_time = datetime.now()
            gate = Gate.query.filter_by(id=gate_id).first()
            if not gate:
                return render_template("index.html", message="Gate not found")
            new_person_request = Person(
                first_name,
                last_name,
                email,
                gate_id,
                reason,
                request_time,
                entry_given,
                entry_given_time,
            )
            db.session.add(new_person_request)
            db.session.commit()

            msg = "Successfully"

            controllers = GateAccess.query.filter_by(gate_id=gate_id).all()
            for controller in controllers:
                controller_id = controller.controller_id
                person_id = new_person_request.person_id
                approval = False
                new_controller_approval = ControllerApproval(
                    controller_id, person_id, approval
                )
                db.session.add(new_controller_approval)
            db.session.commit()

        except Exception as err:
            msg = "We cannot add the person to the list"

        return render_template("thankyou.html", personid=new_person_request.person_id)
    return render_template("index.html")


@auth.verify_token
def verify_password(sessionkey):
    if Session.query.filter_by(session_id=sessionkey).first() != None:
        return True
    return False


@auth.error_handler
def handle401(error):
    return {"error": "UnAuthorized"}, 401


@app.route("/controller/login", methods=["POST"])
def controllerLogin():
    requestData = request.get_json(force=True)
    email = requestData.get("email")
    password = requestData.get("password")

    if None in [email, password]:
        return jsonify({"error": "Missing email or password"}), 400
    controller = Controller.query.filter_by(email=email).first()
    if not controller:
        return jsonify({"error": "Invalid email"}), 400
    if controller.password_hash != sha256(str(password).encode()).hexdigest():
        return jsonify({"error": "Invalid password"}), 400

    sessionkey = "".join([random.choice(string.ascii_letters) for i in range(20)])
    session = Session(sessionkey, controller.id)
    db.session.add(session)
    db.session.commit()
    return jsonify({"sessionkey": sessionkey}), 200


@app.route(
    "/controller/gaterequest/<int:person_id>/modifyEntryStatus/<int:state>",
    methods=["POST"],
)
@auth.login_required
def changeEntryStatus(person_id, state):
    if state not in [0, 1]:
        return jsonify({"error": "Invalid state"}), 400
    session = Session.query.filter_by(
        session_id=request.headers.get("Authentication")
    ).first()
    if not session:
        return jsonify({"error": "Invalid session"}), 400
    controller = Controller.query.filter_by(id=session.controller_id).first()
    person = Person.query.filter_by(person_id=person_id).first()
    gateaccess = GateAccess.query.filter_by(
        controller_id=controller.id, gate_id=person.gate_id
    ).first()
    if not gateaccess:
        return jsonify({"error": "You don't have access to this gate"}), 400
    controllerApproval = ControllerApproval.query.filter_by(
        person_id=person.person_id, controller_id=controller.id
    ).first()
    if not controllerApproval:
        return jsonify({"error": "You don't have access to this person"}), 400
    controllerApproval.approval = True if state else False
    controllerApproval.approval_time = datetime.now()
    db.session.add(controllerApproval)
    db.session.commit()
    return {"message": "success"}, 200


@app.route("/controller/gaterequest/<int:person_id>/status")
def getEntryStatus(person_id):
    person = Person.query.filter_by(person_id=person_id).first()
    if not person:
        return jsonify({"error": "Invalid person id"}), 400
    controllers = ControllerApproval.query.filter_by(person_id=person.person_id).all()
    allAccepted = True
    acceptances = {}
    for controller in controllers:
        acceptances[controller.controller_id] = controller.approval
        if not controller.approval:
            allAccepted = False
    return jsonify({"allAccepted": allAccepted, "acceptances": acceptances}), 200


# Controller Logs In through /controller/login
#             |
#             V
# Controller gets a session key
#             |
#             V
# Controller uses the session key to access the gate request through /controller/gaterequest/<person_id:int>/modifyEntryStatus/<state:int> with the session key as the Authentication header
#             |
#             V
# The frontend polls the /controller/gaterequest/<person_id:int>/status endpoint from the thankyou.html page to get the status of the request
#             |
#             V
# The frontend can make use of the allAccepted field to determine whether the request has been accepted or not
# and
# The frontend can make use of the acceptances fields to determine which controllers have accepted the request with the controller id as the key and the value being the acceptance status


@app.route("/thankyou")
def thankyou_page():
    return render_template("thankyou.html")


#
if __name__ == "__main__":
    app.run(debug=True)
