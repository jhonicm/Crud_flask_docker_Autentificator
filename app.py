from flask import Flask, request, jsonify
from models import db, User
from flask_cors import CORS  # Importar Flask-CORS
from config import Config


app = Flask(__name__)
app.config.from_object(Config)
CORS(app, resources={r"/users/*": {"origins": "http://localhost:8080"}}, methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])

db.init_app(app)
with app.app_context():
    db.create_all()

@app.route('/users', methods=['POST'])
def create_user():
    try:
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
        new_user = User(
            username=data['username'],
            email=data['email'],
            password=data['password']
        )
        db.session.add(new_user)
        db.session.commit()
        return "<h1>Usuario creado exitosamente!</h1>", 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/users', methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify([{'id': user.id, 'username': user.username, 'email': user.email} for user in users])

@app.route('/users/<int:id>', methods=['GET'])
def get_user(id):
    user = User.query.get_or_404(id)
    return jsonify({'id': user.id, 'username': user.username, 'email': user.email})

@app.route('/users/<int:id>', methods=['PUT'])
def update_user(id):
    data = request.get_json()
    user = User.query.get_or_404(id)
    user.username = data['username']
    user.email = data['email']
    db.session.commit()
    return jsonify({'message': 'User updated successfully'})

@app.route('/users/<int:id>', methods=['DELETE'])
def delete_user(id):
    try:
        user = User.query.get_or_404(id)
        db.session.delete(user)
        db.session.commit()
        return jsonify({'message': 'User deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)