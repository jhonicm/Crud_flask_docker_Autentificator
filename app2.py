from flask import Flask, request, jsonify
from models import db, Product
from flask_cors import CORS 
from config import Config
 
app = Flask(__name__)
app.config.from_object(Config)
CORS(app, resources={r"/products*": {"origins": "http://localhost:8080"}})  # Configurar CORS para las rutas de productos
db.init_app(app)

with app.app_context():
    db.create_all(bind_key='products')


@app.route('/products', methods=['POST'])
def create_product():
    try:
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
        new_product = Product(
            name=data['name'],
            price=float(data['price']),
            description=data.get("description", ""),
            stock=int(data.get("stock", 0))
        )
        db.session.add(new_product)
        db.session.commit()
        return "<h1>Producto creado exitosamente!</h1>", 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
    
@app.route('/products', methods=['GET'])
def get_products():  
    products = Product.query.all()
    return jsonify([{'id': product.id, 'name': product.name, 'price': product.price, 'description': product.description, 'stock': product.stock} for product in products])

@app.route('/products/<int:id>', methods=['GET'])
def get_product_by_id(id):
    product = Product.query.get_or_404(id)
    return jsonify({'id': product.id, 'name': product.name, 'price': product.price, 'description': product.description, 'stock': product.stock})

@app.route('/products/<int:id>', methods=['PUT'])
def update_product(id):
    data = request.get_json()
    product = Product.query.get_or_404(id)
    product.name = data['name']
    product.price = data['price']
    product.description = data.get('description', product.description)
    product.stock = data.get('stock', product.stock)
    db.session.commit()
    return jsonify({'message': 'Product updated successfully'})

@app.route('/products/<int:id>', methods=['DELETE'])
def delete_product(id):
    product = Product.query.get_or_404(id)
    db.session.delete(product)
    db.session.commit()
    return jsonify({'message': 'Product deleted successfully'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)