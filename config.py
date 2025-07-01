import os

class Config:
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'postgresql://myuser:mypassword@db:5432/mydatabase'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    SQLALCHEMY_BINDS = {
        'products': os.getenv('PRODUCTS_DATABASE_URL') or 'postgresql://productuser:productpass@products_db:5432/productsdb'
    }   
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False