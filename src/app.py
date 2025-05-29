"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
from sqlalchemy import select
from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, User, TokenBlockedList
from flask_bcrypt import Bcrypt
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
    if user_data["name"] is None:
        return jsonify({"message": "No name entered"}), 400
    if user_data["email"] is None:
        return jsonify({"message": "No email entered"}), 400
    if user_data["password"] is None:
        return jsonify({"message": "No password entered"}), 400

    user_data["password"] = bcrypt.generate_password_hash(
        user_data["password"]).decode('utf-8')
    new_user = User(
        name=user_data["name"],
        email=user_data["email"],
        password=user_data["password"],
        is_active=True)

    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "Successful registration"}), 201


@app.route('/login', methods=['POST'])
def login_user():
    login_data = request.get_json()

    if login_data["email"] is None:
        return jsonify({"message": "No email entered"}), 400
    if login_data["password"] is None:
        return jsonify({"message": "No password entered"}), 400

    user = db.session.execute(select(User).where(
        User.email == login_data["email"])).scalar_one()
    if user is None:
        return jsonify({"message": "User not found"}), 401
    valid_password = bcrypt.check_password_hash(
        user.password, login_data["password"])
    if not valid_password:
        return jsonify({"message": "Invalid password"}), 401

    token = create_access_token(
        identity=user.id,
        additional_claims={"role": "admin"})

    return jsonify({"token": token, "user_id": user.id})


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
