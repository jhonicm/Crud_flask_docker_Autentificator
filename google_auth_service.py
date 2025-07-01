import io
import time
import pyotp
import qrcode
import base64
from flask import Flask, render_template_string, request

app = Flask(__name__)
app.secret_key = "TU_SECRETO"

# Usa una clave secreta FIJA para pruebas
SECRET = "JBSWY3DPEHPK3PXP"  # Puedes cambiarla, pero mantenla igual durante las pruebas

@app.route("/")
def index():
    totp = pyotp.TOTP(SECRET)
    uri = totp.provisioning_uri(name="usuario@example.com", issuer_name="MiAplicacion")
    img = qrcode.make(uri)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    qr_data = base64.b64encode(buffer.getvalue()).decode("utf-8")
    html = f"""
    <h2>Escanea este QR con Google Authenticator</h2>
    <img src="data:image/png;base64,{qr_data}" /><br>
    <p>O usa la clave secreta: <b>{SECRET}</b></p>
    <h3>Verificar código</h3>
    <form method="POST" action="/verify">
      <input type="text" name="token" placeholder="Código" required>
      <button type="submit">Verificar</button>
    </form>
    """
    return render_template_string(html)

@app.route("/verify", methods=["POST"])
def verify():
    token = request.form.get("token")
    totp = pyotp.TOTP(SECRET)
    current_code = totp.now()
    now = int(time.time())
    print("Token recibido:", token)
    print("Token esperado (actual):", current_code)
    print("Token válido anterior:", totp.at(now - 30))
    print("Token válido siguiente:", totp.at(now + 30))
    if totp.verify(token):
        msg = "<p style='color:green;'>¡Código válido!</p>"
    else:
        msg = "<p style='color:red;'>Código inválido.</p>"
    return render_template_string(f"{msg}<a href='/'>Volver</a>")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5003)