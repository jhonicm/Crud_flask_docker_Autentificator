import psycopg2
from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.parse
import os
from http import cookies
import pyotp
import qrcode
import io
import base64
import json

# Configuración de la base de datos de usuarios
USERS_DB_HOST = "localhost"
USERS_DB_NAME = "mydatabase"
USERS_DB_USER = "myuser"
USERS_DB_PASS = "mypassword"

# Configuración de la base de datos de productos
PRODUCTS_DB_HOST = "localhost"
PRODUCTS_DB_NAME = "productsdb"
PRODUCTS_DB_USER = "productuser"
PRODUCTS_DB_PASS = "productpass"
PRODUCTS_DB_PORT = 5433

# Rutas de los archivos HTML
HTML_LOGIN = os.path.join(os.path.dirname(__file__), "login.html")
HTML_PRODUCTS = os.path.join(os.path.dirname(__file__), "products.html")

def cargar_html(path, msg=""):
    with open(path, encoding="utf-8") as f:
        html = f.read()
    return html.replace("{msg}", msg)

def generar_qr(secret, username, issuer="MiAplicacion"):
    totp = pyotp.TOTP(secret)
    uri = totp.provisioning_uri(name=username, issuer_name=issuer)
    img = qrcode.make(uri)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    qr_data = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return qr_data

def cargar_html_verificar(username, secret, msg=""):
    qr_data = generar_qr(secret, username)
    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <title>Verificar Código</title>
</head>
<body>
  <div class="login-container">
    <h2>Bienvenido {username}</h2>
    <h3>Escanea este QR con Google Authenticator</h3>
    <img src="data:image/png;base64,{qr_data}" /><br>
    <p>O introduce manualmente la clave secreta: <b>{secret}</b></p>
    <h3>Ingrese el código de autenticación</h3>
    <form method="POST" action="/">
      <input type="hidden" name="fase" value="verify">
      <input type="hidden" name="username" value="{username}">
      <input type="text" name="token" placeholder="Código" required>
      <button type="submit">Verificar</button>
    </form>
    {msg}
  </div>
</body>
</html>"""
    return html

def validar_usuario(email, password):
    try:
        conn = psycopg2.connect(
            host=USERS_DB_HOST,
            dbname=USERS_DB_NAME,
            user=USERS_DB_USER,
            password=USERS_DB_PASS
        )
        cur = conn.cursor()
        cur.execute('SELECT username, email, password, secret FROM "user" WHERE email=%s AND password=%s', (email, password))
        user = cur.fetchone()
        if user:
            username, db_email, db_password, db_secret = user
            if not db_secret:
                new_secret = pyotp.random_base32()
                cur.execute('UPDATE "user" SET secret=%s WHERE email=%s', (new_secret, email))
                conn.commit()
                db_secret = new_secret
            cur.close()
            conn.close()
            role = "admin" if db_email.strip().lower() == "admin@gmail.com" else "user"
            return role, username, db_secret, db_email
        cur.close()
        conn.close()
        return None, None, None, None
    except Exception as e:
        print("Error validando usuario:", e)
        return None, None, None, None

def listar_productos():
    try:
        conn = psycopg2.connect(
            host=PRODUCTS_DB_HOST,
            port=PRODUCTS_DB_PORT,
            dbname=PRODUCTS_DB_NAME,
            user=PRODUCTS_DB_USER,
            password=PRODUCTS_DB_PASS
        )
        cur = conn.cursor()
        cur.execute('SELECT id, name, price, description, stock FROM product')
        productos = cur.fetchall()
        cur.close()
        conn.close()
        return productos
    except Exception as e:
        print("Error al listar productos:", e)
        return []

def listar_usuarios():
    try:
        conn = psycopg2.connect(
            host=USERS_DB_HOST,
            dbname=USERS_DB_NAME,
            user=USERS_DB_USER,
            password=USERS_DB_PASS
        )
        cur = conn.cursor()
        cur.execute('SELECT id, username, email FROM "user"')
        usuarios = cur.fetchall()
        cur.close()
        conn.close()
        return usuarios
    except Exception as e:
        print("Error al listar usuarios:", e)
        return []

def renderizar_productos(productos, es_admin=False):
    if not productos:
        return "<p>No hay productos registrados.</p>"
    html = """
    <h3>Productos</h3>
    <table>
      <tr>
        <th>ID</th>
        <th>Nombre</th>
        <th>Precio</th>
        <th>Descripción</th>
        <th>Stock</th>
    """
    if es_admin:
        html += "<th>Acciones</th>"
    html += "</tr>"
    for prod in productos:
        html += f"""
        <tr data-id="{prod[0]}" data-name="{prod[1]}" data-price="{prod[2]}" data-description="{prod[3]}" data-stock="{prod[4]}">
          <td>{prod[0]}</td>
          <td>{prod[1]}</td>
          <td>{prod[2]}</td>
          <td>{prod[3]}</td>
          <td>{prod[4]}</td>
        """
        if es_admin:
            html += """
            <td>
              <button class="edit-btn">Editar</button>
              <button class="delete-btn">Eliminar</button>
            </td>
            """
        html += "</tr>"
    html += "</table>"
    return html

def renderizar_usuarios(usuarios):
    if not usuarios:
        return "<p>No hay usuarios registrados.</p>"
    html = """
    <h3>Usuarios</h3>
    <table border='1' cellpadding='5'>
      <tr>
        <th>ID</th>
        <th>Username</th>
        <th>Email</th>
        <th>Acciones</th>
      </tr>
    """
    for user in usuarios:
        html += f"""
        <tr data-id="{user[0]}" data-username="{user[1]}" data-email="{user[2]}">
          <td>{user[0]}</td>
          <td>{user[1]}</td>
          <td>{user[2]}</td>
          <td>
            <button class="edit-user-btn">Editar</button>
            <button class="delete-user-btn">Eliminar</button>
          </td>
        </tr>
        """
    html += "</table>"
    return html

def renderizar_admin_forms():
    return """
    <button id="show-create-user" class="add-button">Añadir Usuario</button>
    <button id="show-create-product" class="add-button">Añadir Producto</button>
    <hr>
    <div id="create-user-div" style="display:none;">
      <h3>Crear Usuario</h3>
      <form id="create-user-form">
        <label>Username:</label><br>
        <input type="text" name="username" required><br>
        <label>Email:</label><br>
        <input type="email" name="email" required><br>
        <label>Password:</label><br>
        <input type="password" name="password" required><br>
        <button type="submit">Crear Usuario</button>
        <button type="button" id="cancel-create-user">Cancelar</button>
      </form>
      <div id="user-message"></div>
    </div>
    
    <div id="edit-user-div" style="display:none;">
      <h3>Editar Usuario</h3>
      <form id="edit-user-form">
        <input type="hidden" name="id" id="edit-user-id">
        <label>Username:</label><br>
        <input type="text" name="username" id="edit-user-username" required><br>
        <label>Email:</label><br>
        <input type="email" name="email" id="edit-user-email" required><br>
        <button type="submit">Actualizar Usuario</button>
        <button type="button" id="cancel-edit-user">Cancelar</button>
      </form>
      <div id="edit-user-message"></div>
    </div>
    
    <div id="create-product-div" style="display:none;">
      <h3>Crear Producto</h3>
      <form id="create-product-form">
        <label>Nombre:</label><br>
        <input type="text" name="name" required><br>
        <label>Precio:</label><br>
        <input type="number" name="price" step="0.01" required><br>
        <label>Descripción:</label><br>
        <textarea name="description"></textarea><br>
        <label>Stock:</label><br>
        <input type="number" name="stock" required><br>
        <button type="submit">Crear Producto</button>
        <button type="button" id="cancel-create-product">Cancelar</button>
      </form>
      <div id="product-message"></div>
    </div>
    
    <div id="edit-product-div" style="display:none;">
      <h3>Editar Producto</h3>
      <form id="edit-product-form">
        <input type="hidden" name="id" id="edit-product-id">
        <label>Nombre:</label><br>
        <input type="text" name="name" id="edit-product-name" required><br>
        <label>Precio:</label><br>
        <input type="number" name="price" id="edit-product-price" step="0.01" required><br>
        <label>Descripción:</label><br>
        <textarea name="description" id="edit-product-description"></textarea><br>
        <label>Stock:</label><br>
        <input type="number" name="stock" id="edit-product-stock" required><br>
        <button type="submit">Actualizar Producto</button>
        <button type="button" id="cancel-edit-product">Cancelar</button>
      </form>
      <div id="edit-product-message"></div>
    </div>
    
    <script>
      // Mostrar formularios al hacer clic en "Añadir"
      document.getElementById('show-create-user').addEventListener('click', function() {
          document.getElementById('create-user-div').style.display = 'block';
      });
      document.getElementById('show-create-product').addEventListener('click', function() {
          document.getElementById('create-product-div').style.display = 'block';
      });
      
      // Cancelar creación
      document.getElementById('cancel-create-user').addEventListener('click', function() {
          document.getElementById('create-user-form').reset();
          document.getElementById('create-user-div').style.display = 'none';
          document.getElementById('user-message').innerHTML = '';
      });
      document.getElementById('cancel-create-product').addEventListener('click', function() {
          document.getElementById('create-product-form').reset();
          document.getElementById('create-product-div').style.display = 'none';
          document.getElementById('product-message').innerHTML = '';
      });
      
      // Cancelar edición
      document.getElementById('cancel-edit-product').addEventListener('click', function() {
          document.getElementById('edit-product-form').reset();
          document.getElementById('edit-product-div').style.display = 'none';
          document.getElementById('edit-product-message').innerHTML = '';
      });
      document.getElementById('cancel-edit-user').addEventListener('click', function() {
          document.getElementById('edit-user-form').reset();
          document.getElementById('edit-user-div').style.display = 'none';
          document.getElementById('edit-user-message').innerHTML = '';
      });
      
      // Crear Usuario
      document.getElementById('create-user-form').addEventListener('submit', function(e) {
        e.preventDefault();
        const formData = new FormData(this);
        fetch('http://localhost:5000/users', {
          method: 'POST',
          body: formData
        })
        .then(response => {
          if (response.ok) { return response.text(); }
          else { throw new Error("Error en la respuesta del servidor"); }
        })
        .then(data => {
          document.getElementById('user-message').innerHTML = data;
          setTimeout(function(){
              document.getElementById('create-user-form').reset();
              document.getElementById('create-user-div').style.display = 'none';
              location.reload();
          }, 1500);
        })
        .catch(error => {
          console.error(error);
          document.getElementById('user-message').innerHTML = "Error al crear el usuario.";
        });
      });
      
      // Editar Usuario
      document.getElementById('edit-user-form').addEventListener('submit', function(e) {
        e.preventDefault();
        const userId = document.getElementById('edit-user-id').value;
        const formData = {
          username: document.getElementById('edit-user-username').value,
          email: document.getElementById('edit-user-email').value
        };
        fetch('http://localhost:5000/users/' + userId, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(formData)
        })
        .then(response => response.json())
        .then(data => {
          document.getElementById('edit-user-message').innerHTML = data.message || data.error;
          setTimeout(function(){ location.reload(); }, 1500);
        })
        .catch(error => {
          console.error(error);
          document.getElementById('edit-user-message').innerHTML = "Error al editar el usuario.";
        });
      });
      
      // Crear Producto
      document.getElementById('create-product-form').addEventListener('submit', function(e) {
        e.preventDefault();
        const formData = new FormData(this);
        fetch('http://localhost:5001/products', {
          method: 'POST',
          body: formData
        })
        .then(response => {
          if (response.ok) { return response.text(); }
          else { throw new Error("Error en la respuesta del servidor"); }
        })
        .then(data => {
          document.getElementById('product-message').innerHTML = data;
          setTimeout(function(){
              document.getElementById('create-product-form').reset();
              document.getElementById('create-product-div').style.display = 'none';
              location.reload();
          }, 1500);
        })
        .catch(error => {
          console.error(error);
          document.getElementById('product-message').innerHTML = "Error al crear el producto.";
        });
      });
      
      // Editar Producto
      document.getElementById('edit-product-form').addEventListener('submit', function(e) {
        e.preventDefault();
        const prodId = document.getElementById('edit-product-id').value;
        const formData = {
          name: document.getElementById('edit-product-name').value,
          price: parseFloat(document.getElementById('edit-product-price').value),
          description: document.getElementById('edit-product-description').value,
          stock: parseInt(document.getElementById('edit-product-stock').value)
        };
        fetch('http://localhost:5001/products/' + prodId, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(formData)
        })
        .then(response => response.json())
        .then(data => {
          document.getElementById('edit-product-message').innerHTML = data.message || data.error;
          setTimeout(function(){ location.reload(); }, 1500);
        })
        .catch(error => {
          console.error(error);
          document.getElementById('edit-product-message').innerHTML = "Error al editar el producto.";
        });
      });
      
      // Delegación de eventos para Editar y Eliminar Producto
      document.addEventListener('click', function(e) {
        if(e.target && e.target.classList.contains('edit-btn')) {
          const tr = e.target.closest('tr');
          document.getElementById('edit-product-id').value = tr.getAttribute('data-id');
          document.getElementById('edit-product-name').value = tr.getAttribute('data-name');
          document.getElementById('edit-product-price').value = tr.getAttribute('data-price');
          document.getElementById('edit-product-description').value = tr.getAttribute('data-description');
          document.getElementById('edit-product-stock').value = tr.getAttribute('data-stock');
          document.getElementById('edit-product-div').style.display = 'block';
        }
        if(e.target && e.target.classList.contains('delete-btn')) {
          const tr = e.target.closest('tr');
          const prodId = tr.getAttribute('data-id');
          if(confirm('¿Estás seguro de eliminar este producto?')) {
            fetch('http://localhost:5001/products/' + prodId, { method: 'DELETE' })
            .then(response => response.json())
            .then(data => { alert(data.message || data.error); location.reload(); })
            .catch(error => { console.error(error); alert("Error al eliminar el producto."); });
          }
        }
      });
      
      // Delegación de eventos para Editar y Eliminar Usuario
      document.addEventListener('click', function(e) {
        if(e.target && e.target.classList.contains('edit-user-btn')) {
          const tr = e.target.closest('tr');
          document.getElementById('edit-user-id').value = tr.getAttribute('data-id');
          document.getElementById('edit-user-username').value = tr.getAttribute('data-username');
          document.getElementById('edit-user-email').value = tr.getAttribute('data-email');
          document.getElementById('edit-user-div').style.display = 'block';
        }
        if(e.target && e.target.classList.contains('delete-user-btn')) {
          const tr = e.target.closest('tr');
          const userId = tr.getAttribute('data-id');
          if(confirm('¿Está seguro de eliminar este usuario?')) {
            fetch('http://localhost:5000/users/' + userId, { method: 'DELETE' })
            .then(response => response.json())
            .then(data => { alert(data.message || data.error); location.reload(); })
            .catch(error => { console.error(error); alert("Error al eliminar el usuario."); });
          }
        }
      });
    </script>
    """

class LoginHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        c = cookies.SimpleCookie(self.headers.get('Cookie'))
        fase = c.get('fase')
        role = c.get('role')
        user = c.get('user')

        if not role:
            # No autenticado: mostrar login
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(cargar_html(HTML_LOGIN).encode("utf-8"))
        else:
            # Ya autenticado: mostrar panel según rol
            if role.value == "admin":
                usuarios = listar_usuarios()
                productos = listar_productos()
                contenido = (
                    renderizar_usuarios(usuarios)
                    + "<br>" + renderizar_productos(productos, es_admin=True)
                    + "<br>" + renderizar_admin_forms()
                )
            elif role.value == "user":
                productos = listar_productos()
                contenido = renderizar_productos(productos, es_admin=False)
            else:
                contenido = "<p>Error: Rol no reconocido.</p>"
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(cargar_html(HTML_PRODUCTS, contenido).encode("utf-8"))

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        params = urllib.parse.parse_qs(post_data.decode('utf-8'))

        fase = params.get('fase', ['login'])[0]

        if fase == "login":
            email = params.get('email', [''])[0].strip().lower()
            password = params.get('password', [''])[0]
            role, username, user_secret, db_email = validar_usuario(email, password)
            if role:
                qr_data = generar_qr(user_secret, username)
                self.send_response(200)
                self.send_header("Content-type", "application/json; charset=utf-8")
                self.send_header("Set-Cookie", f"user={username}; Path=/")
                self.send_header("Set-Cookie", f"fase=verify; Path=/")
                self.end_headers()
                self.wfile.write(json.dumps({
                    "qr": qr_data,
                    "secret": user_secret,
                    "username": username
                }).encode("utf-8"))
            else:
                self.send_response(200)
                self.send_header("Content-type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({
                    "error": "Email o contraseña incorrectos."
                }).encode("utf-8"))
        elif fase == "verify":
            username = params.get('username', [''])[0]
            token = params.get('token', [''])[0]
            try:
                conn = psycopg2.connect(
                    host=USERS_DB_HOST,
                    dbname=USERS_DB_NAME,
                    user=USERS_DB_USER,
                    password=USERS_DB_PASS
                )
                cur = conn.cursor()
                cur.execute('SELECT secret, email FROM "user" WHERE username=%s', (username,))
                user_row = cur.fetchone()
                cur.close()
                conn.close()
            except Exception as e:
                print("Error obteniendo secret:", e)
                user_row = None

            if user_row:
                user_secret, email = user_row
                totp = pyotp.TOTP(user_secret)
                if totp.verify(token):
                    rol = "admin" if email.strip().lower() == "admin@gmail.com" else "user"
                    self.send_response(200)
                    self.send_header("Content-type", "application/json; charset=utf-8")
                    self.send_header("Set-Cookie", f"role={rol}; Path=/")
                    self.send_header("Set-Cookie", "fase=; Path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT")
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        "success": "¡Autenticación exitosa!"
                    }).encode("utf-8"))
                    return
                else:
                    self.send_response(200)
                    self.send_header("Content-type", "application/json; charset=utf-8")
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        "error": "Código inválido."
                    }).encode("utf-8"))
                    return
            self.send_response(200)
            self.send_header("Content-type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps({
                "error": "Error de autenticación."
            }).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()
if __name__ == "__main__":
    server_address = ('', 8080)
    httpd = HTTPServer(server_address, LoginHandler)
    print("Servidor corriendo en http://localhost:8080")
    httpd.serve_forever()