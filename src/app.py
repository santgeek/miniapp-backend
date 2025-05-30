"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
from sqlalchemy import select
from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from .utils import APIException, generate_sitemap
from .admin import setup_admin
from .models import db, User, TokenBlockedList
from flask_bcrypt import Bcrypt
from sqlalchemy.exc import NoResultFound
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, get_jwt, JWTManager


app = Flask(__name__)
bcrypt = Bcrypt(app)
app.url_map.strict_slashes = False

app.config["JWT_SECRET_KEY"] = "polar bear"
jwt = JWTManager(app)

db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace(
        "postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"

# --- START OF TEMPORARY DEBUG CODE ---
# CAUTION: This will print your database credentials (username, password, host)
# to your public Render logs.
# YOU MUST REMOVE THESE LINES IMMEDIATELY AFTER DIAGNOSIS!
print(
    f"DEBUGGING DATABASE_URL (FROM APP.PY): {app.config['SQLALCHEMY_DATABASE_URI']}")
# --- END OF TEMPORARY DEBUG CODE ---

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)


@app.before_request
def handle_options_request():
    if request.method == 'OPTIONS':
        return '', 204

# Handle/serialize errors like a JSON object


@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# generate sitemap with all your endpoints


@app.route('/')
def sitemap():
    return generate_sitemap(app)


@app.route('/user', methods=['GET'])
def handle_users():
    all_users = User.query.all()
    serialized_users = [user.to_dict() for user in all_users]

    return jsonify(serialized_users), 200


@app.route('/register', methods=['POST'])
def add_user():
    user_data = request.get_json()
    if not user_data:
        return jsonify({"message": "Invalid JSON or empty request body"}), 400

    name = user_data.get("name")
    email = user_data.get("email")
    password = user_data.get("password")

    if name is None:
        return jsonify({"message": "No name entered"}), 400
    if email is None:
        return jsonify({"message": "No email entered"}), 400
    if password is None:
        return jsonify({"message": "No password entered"}), 400

    if "@" not in email or "." not in email:
        return jsonify({"message": "Invalid mail format"}), 400

    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({"message": "User already registered"}), 409

    if len(password) < 6:
        return jsonify({"message": "Password must have a minimum of 6 characters"})

    try:
        hashed_password = bcrypt.generate_password_hash(
            password).decode('utf-8')

        new_user = User(
            name=name,
            email=email,
            password=hashed_password,
            is_active=True
        )

        db.session.add(new_user)
        db.session.commit()

        return jsonify({"message": "Successful registration", "user_id": new_user.id}), 201

    except Exception as e:
        db.session.rollback()
        print(f"Registration error: {e}")
        return jsonify({"message": "Failed registration"}), 500


@app.route('/login', methods=['POST'])
def login_user():
    login_data = request.get_json()

    if not login_data:
        return jsonify({"message": "Invalid JSON or empty request body"}), 400

    email = login_data.get("email")
    password = login_data.get("password")

    if email is None:
        return jsonify({"message": "No email entered"}), 400
    if password is None:
        return jsonify({"message": "No password entered"}), 400

    user = None

    try:
        user = db.session.execute(select(User).where(
            User.email == email)).scalar_one_or_none()
        if user is None:
            return jsonify({"message": "Invalid credentials"}), 401

        valid_password = bcrypt.check_password_hash(user.password, password)
        if not valid_password:
            return jsonify({"message": "Invalid credentials"}), 401

        token = create_access_token(
            identity=user.id,
            # additional_claims={"role": "admin"}
        )

        return jsonify({"token": token, "user_id": user.id, "message": "Login successful"}), 200

    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({"message": "Failed login. Please try again later"}), 500


@app.route('/admin', methods=['GET'])
@jwt_required()
def access_admin():
    current_user_id = get_jwt_identity()
    token_info = get_jwt()
    user = db.session.get(User, current_user_id)

    return jsonify({"user_data": user.serialize(), "role": token_info["role"]}), 200


@app.route("/logout", methods=['POST'])
@jwt_required()
def user_logout():
    token_data = get_jwt()
    token_blocked = TokenBlockedList(jti=token_data["jti"])
    db.session.add(token_blocked)
    db.session.commit()
    return jsonify({"message": "Session closed"})


# this only runs if `$ python src/app.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)
