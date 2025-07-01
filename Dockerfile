# Usar la imagen oficial de Python como base
FROM python:3.9-slim


# Establecer el directorio de trabajo
WORKDIR /app

# Copiar los archivos requeridos
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto de la aplicación
COPY . .

# Exponer todos los puertos que podrías usar (ajusta según tus servicios)
EXPOSE 5000
EXPOSE 5001
EXPOSE 5003

# Comando para ejecutar la aplicación (usando variable de entorno)
CMD ["sh", "-c", "python ${APP_FILE:-app.py}"]