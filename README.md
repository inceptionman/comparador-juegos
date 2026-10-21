# Comparador de precios de videojuegos

Aplicación web académica para buscar videojuegos, comparar ofertas y guardar una lista de deseos con un precio objetivo. El backend usa FastAPI, SQLAlchemy asíncrono, SQLite por defecto y la API de IsThereAnyDeal como fuente externa.

## Arquitectura

- `app/routers`: búsqueda y datos de inicio.
- `app/auth`: registro, inicio/cierre de sesión y JWT en cookie `HttpOnly`.
- `app/wishlist`: operaciones protegidas de la lista de deseos.
- `app/services`: integración externa y persistencia.
- `app/repositories`: acceso a datos.
- `app/db`: modelos SQLAlchemy y sesión.
- `app/templates`: interfaz HTML/Jinja.
- `alembic/versions`: migraciones versionadas.

Al buscar un juego, la aplicación consulta IsThereAnyDeal, normaliza el resultado y persiste el juego, las tiendas, las plataformas y las ofertas disponibles. Esto permite que el mismo juego se agregue posteriormente a la lista de deseos sin inventar precios.

## Configuración y ejecución

1. Crear un entorno virtual e instalar dependencias:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

2. Copiar `.env.example` a `.env` y configurar `ITAD_API_KEY` y `JWT_SECRET_KEY`. En producción, usar `COOKIE_SECURE=true` junto con HTTPS.

3. Aplicar las migraciones:

   ```powershell
   alembic upgrade head
   ```

4. Iniciar el servidor:

   ```powershell
   uvicorn app.main:app --reload
   ```

## Endpoints principales

| Método | Ruta | Uso |
|---|---|---|
| `GET` | `/` | Interfaz de búsqueda |
| `GET` | `/buscar?q=...` | Buscar y comparar ofertas |
| `POST` | `/api/auth/register` | Crear cuenta |
| `POST` | `/api/auth/login` | Iniciar sesión |
| `POST` | `/api/auth/logout` | Expirar la cookie de sesión |
| `GET` | `/api/auth/me` | Consultar usuario autenticado |
| `GET` | `/api/wishlist` | Consultar la lista propia |
| `POST` | `/api/wishlist` | Guardar un juego |
| `PATCH` | `/api/wishlist/{item_id}` | Cambiar precio objetivo |
| `DELETE` | `/api/wishlist/{item_id}` | Eliminar un elemento |
| `GET` | `/api/wishlist/page` | Interfaz de lista de deseos |

Ejemplo para guardar un juego:

```json
{
  "game_id": "00000000-0000-0000-0000-000000000000",
  "target_price": 19.99,
  "currency": "USD"
}
```

Las operaciones de lista requieren la cookie creada al registrarse o iniciar sesión. El servidor obtiene el usuario desde el JWT y nunca acepta un `user_id` enviado por el cliente. Los precios objetivo son finitos, no negativos y se comparan únicamente con ofertas disponibles en la misma moneda.

## Pruebas

```powershell
pytest -q
```

El conjunto actual cubre modelos, repositorios, persistencia, caché, migraciones y expiración de la sesión. La API externa puede no estar disponible durante las pruebas; en ese caso la interfaz muestra un mensaje y la lista local sigue funcionando.

## Limitaciones conocidas

- La disponibilidad y exactitud de las ofertas dependen de IsThereAnyDeal y de su clave API.
- El país de consulta está fijado en `US`; la conversión de monedas no se realiza.
- No se envían alertas automáticas por correo, tal como se definió para el MVP.
- La limitación de intentos de inicio de sesión debe añadirse antes de un despliegue público con múltiples réplicas.
