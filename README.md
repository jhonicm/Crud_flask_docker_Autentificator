# CRUD Flask Docker Autentificator

Este proyecto es una API RESTful desarrollada con **Flask** que implementa operaciones CRUD (Crear, Leer, Actualizar, Eliminar) y autenticación de usuarios. El entorno está completamente dockerizado para facilitar la ejecución y despliegue.

## 🚀 Tecnologías utilizadas

- Python 3
- Flask
- SQLAlchemy
- SQLite (puedes cambiar a otra base de datos)
- Docker & Docker Compose
- JWT (JSON Web Tokens) para autenticación
- Flask-CORS

## 📦 Estructura del proyecto

```
├── app/
│   ├── __init__.py
│   ├── models.py
│   ├── routes.py
│   ├── auth.py
│   └── ...
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```

## ⚙️ Instalación y ejecución

### 1. Clona el repositorio

```bash
git clone https://github.com/jhonicm/Crud_flask_docker_Autentificator.git
cd Crud_flask_docker_Autentificator
```

### 2. Construye y ejecuta con Docker

```bash
docker-compose up --build
```

Esto levantará el backend de Flask en el puerto `5000`.

### 3. Accede a la API

La API estará disponible en:  
```
http://localhost:5000/
```

## 🔑 Endpoints principales

- `POST /login` — Autenticación de usuario (devuelve JWT)
- `GET /users` — Listar usuarios (requiere autenticación)
- `POST /users` — Crear usuario
- `GET /users/<id>` — Obtener usuario por ID
- `PUT /users/<id>` — Actualizar usuario
- `DELETE /users/<id>` — Eliminar usuario

> **Nota:** Algunos endpoints requieren el token JWT en el header `Authorization`.

