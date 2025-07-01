import psycopg2

DB_HOST = "localhost"
DB_NAME = "productsdb"
DB_USER = "productuser"
DB_PASS = "productpass"

def listar_productos():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=5433,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASS
        )
        cur = conn.cursor()
        cur.execute('SELECT name, price, description, stock FROM product')
        productos = cur.fetchall()
        cur.close()
        conn.close()
        return productos
    except Exception as e:
        print("Error al conectar a la base de datos:", e)
        return []

if __name__ == "__main__":
    productos = listar_productos()
    if productos:
        print("Nombre | Precio | Descripción | Stock")
        for prod in productos:
            print(f"{prod[0]} | {prod[1]} | {prod[2] }| {prod[3]}")
    else:
        print("No hay productos registrados.")