# Sprint: Autenticación JWT y lista de deseos con precio objetivo

## 1. Contexto del proyecto

Estoy desarrollando una aplicación web de comparación de precios de videojuegos, similar a GG.deals, IsThereAnyDeal y CheapShark. El objetivo es que los usuarios puedan consultar videojuegos, comparar precios entre distintas tiendas y guardar los juegos que les interesan para realizar un seguimiento de sus precios.

En este sprint se implementarán dos funcionalidades principales:

1. Registro e inicio de sesión con autenticación JWT.
2. Lista de deseos personalizada con un precio objetivo por videojuego.

La aplicación debe tener una arquitectura clara, segura, escalable y fácil de mantener.

## 2. Objetivos del sprint

### Funcionalidad A: Registro e inicio de sesión con JWT

Implementar un sistema de autenticación que permita a los usuarios crear una cuenta e iniciar sesión de forma segura.

**Requisitos funcionales:**

- Crear una cuenta con nombre, correo electrónico y contraseña.
- Validar los datos recibidos durante el registro.
- Comprobar que el correo electrónico no esté registrado previamente.
- Cifrar las contraseñas mediante bcrypt o Argon2; nunca almacenarlas en texto plano.
- Permitir el inicio de sesión con correo electrónico y contraseña.
- Generar un JWT firmado después de autenticar correctamente al usuario.
- Proteger las rutas privadas mediante un middleware de autenticación.
- Implementar cierre de sesión y una estrategia adecuada de invalidación o expiración de tokens.
- Devolver mensajes de error claros sin revelar información sensible.
- Validar los permisos para impedir que un usuario acceda a los datos de otro.

**Endpoints sugeridos:**

- `POST /api/auth/register`: registrar un usuario.
- `POST /api/auth/login`: iniciar sesión.
- `POST /api/auth/logout`: cerrar sesión según la estrategia de tokens implementada.
- `GET /api/auth/me`: obtener los datos del usuario autenticado.

**Seguridad:**

- Usar variables de entorno para los secretos JWT.
- Configurar el algoritmo de firma permitido y validar la expiración del token.
- No incluir contraseñas ni datos sensibles en el JWT.
- Aplicar validación de entradas y limitación de intentos de inicio de sesión.
- Si se utiliza una aplicación web, preferir cookies `HttpOnly`, `Secure` y `SameSite` correctamente configuradas, con protección CSRF cuando corresponda. Si se utiliza otro mecanismo de almacenamiento, justificarlo y evitar guardar tokens sensibles en `localStorage`.
- No exponer detalles internos del servidor en las respuestas de error.

### Funcionalidad B: Lista de deseos con precio objetivo

Permitir que cada usuario guarde videojuegos en una lista personal y establezca el precio máximo que está dispuesto a pagar.

**Requisitos funcionales:**

- Añadir un videojuego a la lista de deseos.
- Consultar todos los videojuegos guardados por el usuario autenticado.
- Asignar un precio objetivo a cada videojuego.
- Modificar el precio objetivo de un elemento existente.
- Eliminar videojuegos de la lista.
- Mostrar el precio actual, el precio objetivo y la diferencia entre ambos.
- Mostrar la tienda con el precio más bajo cuando exista información disponible.
- Evitar que el mismo usuario añada duplicados del mismo videojuego.
- Impedir que los usuarios consulten, modifiquen o eliminen elementos pertenecientes a otras cuentas.
- Validar que el precio objetivo sea numérico, finito y mayor o igual que cero.
- Permitir que el usuario consulte si el precio actual ha alcanzado o bajado de su precio objetivo.

**Endpoints sugeridos:**

- `GET /api/wishlist`: consultar la lista personal.
- `POST /api/wishlist`: añadir un videojuego y su precio objetivo.
- `PATCH /api/wishlist/:id`: actualizar el precio objetivo.
- `DELETE /api/wishlist/:id`: eliminar un videojuego.
- `GET /api/wishlist/:id`: consultar el detalle de un elemento, si resulta necesario.

La API debe obtener la identidad del usuario desde el JWT validado, no confiar en un `userId` enviado libremente por el cliente.

### Modelo de datos sugerido

**Tabla `users`**

- `id`: identificador único.
- `name`: nombre del usuario.
- `email`: correo único.
- `password_hash`: contraseña cifrada mediante un algoritmo adecuado.
- `created_at`: fecha de creación.
- `updated_at`: fecha de actualización.

**Tabla `games`**

Reutilizar el catálogo de videojuegos existente. Si todavía no existe, crear una tabla con:

- `id`: identificador único.
- `title`: nombre del videojuego.
- `platform`: plataforma, cuando corresponda.
- `image_url`: imagen de portada, si está disponible.

**Tabla `wishlist_items`**

- `id`: identificador único.
- `user_id`: referencia a `users.id`.
- `game_id`: referencia a `games.id`.
- `target_price`: precio objetivo.
- `currency`: moneda del precio objetivo, por ejemplo COP o USD.
- `created_at`: fecha en que se añadió.
- `updated_at`: última modificación.

Crear una restricción única para `(user_id, game_id)` y las claves foráneas correspondientes.

Si el proyecto ya tiene tablas de precios y tiendas, reutilizarlas para obtener el precio actual más bajo. No duplicar el catálogo ni inventar precios.

## 3. Interfaz de usuario

Implementar las siguientes pantallas:

**Registro**
- Formulario con nombre, correo electrónico y contraseña.
- Validaciones en el cliente y en el servidor.
- Mensajes de error comprensibles.

**Inicio de sesión**
- Formulario de correo electrónico y contraseña.
- Gestión segura de la sesión.
- Acceso a la aplicación después de autenticarse correctamente.

**Lista de deseos**
- Tarjetas o filas con portada, nombre del videojuego y plataforma.
- Precio actual más bajo y tienda correspondiente.
- Campo editable para el precio objetivo.
- Indicador visual cuando el precio actual sea igual o inferior al objetivo.
- Botón para eliminar un juego.
- Estados de carga, lista vacía y errores.

**Integración de navegación**
- Mostrar las opciones de registro e inicio de sesión cuando no haya una sesión activa.
- Mostrar la lista de deseos y la opción de cerrar sesión cuando el usuario esté autenticado.
- Mantener la sesión al recargar la página mediante el mecanismo seguro elegido.

Conservar el sistema de diseño, los componentes y los estilos existentes en el proyecto.

## 4. Reglas de negocio

- Cada lista de deseos pertenece exclusivamente a un usuario.
- Un usuario no puede añadir el mismo videojuego dos veces.
- El precio objetivo se almacena junto con su moneda.
- No comparar directamente cantidades expresadas en monedas diferentes.
- Si no existe un precio actual disponible, mostrar un estado como «Precio no disponible».
- La condición de objetivo alcanzado se cumple cuando el precio actual comparable es menor o igual que el precio objetivo.
- No enviar alertas por correo ni implementar notificaciones automáticas en este sprint, salvo que ya exista infraestructura para ello.
- La lista debe funcionar aunque no haya un servicio externo de precios disponible.

## 5. Pruebas y criterios de aceptación

Implementar pruebas unitarias y de integración para verificar:

**Autenticación**
- El registro exitoso crea un usuario.
- Los correos duplicados son rechazados.
- Las contraseñas nunca se guardan en texto plano.
- El inicio de sesión correcto permite obtener una sesión válida.
- Las credenciales incorrectas son rechazadas.
- Los tokens ausentes, inválidos o expirados no permiten acceder a rutas privadas.
- Las rutas protegidas no filtran datos de otros usuarios.

**Lista de deseos**
- Un usuario autenticado puede añadir un juego y definir su precio objetivo.
- Puede consultar, actualizar y eliminar sus elementos.
- Los usuarios no autenticados no pueden gestionar la lista.
- Un usuario no puede modificar ni eliminar elementos de otra persona.
- Los videojuegos duplicados son rechazados.
- Los precios negativos, no numéricos o infinitos son rechazados.
- Se calcula correctamente la condición de precio objetivo alcanzado.
- Se respetan las monedas y los precios no disponibles.

**Criterio final de aceptación:**

Un usuario puede registrarse, iniciar sesión de forma segura, guardar videojuegos en su lista de deseos, asignar o modificar precios objetivo y consultar si el precio actual disponible cumple su objetivo. Todas las operaciones deben persistir en la base de datos y respetar el aislamiento entre cuentas.

## 6. Instrucciones de implementación

Antes de escribir código:

1. Inspecciona la estructura actual del repositorio.
2. Identifica el frontend, backend, framework, base de datos, sistema de autenticación existente y modelo de videojuegos.
3. Revisa los componentes, convenciones, dependencias y patrones de arquitectura ya utilizados.
4. Presenta un plan breve de implementación adaptado al proyecto real.
5. No reemplaces tecnologías ni reestructures módulos que no sean necesarios para el sprint.

Después:

1. Implementa los cambios en el backend y el frontend.
2. Crea las migraciones necesarias sin destruir datos existentes.
3. Añade validaciones, middleware y controles de autorización.
4. Implementa las pantallas y su integración con la API.
5. Ejecuta las pruebas disponibles, el análisis estático y las comprobaciones de compilación.
6. Corrige los errores introducidos por los cambios.
7. Actualiza el archivo `.env.example` con las variables requeridas, sin incluir secretos reales.
8. Documenta los endpoints, las migraciones, la configuración y los comandos para ejecutar las pruebas.

No inventes endpoints, tablas ni servicios que ya puedan existir. Adapta la solución al código real y evita introducir dependencias innecesarias.

## 7. Entregables

Al finalizar el sprint, proporciona:

- Resumen de funcionalidades implementadas.
- Archivos nuevos y modificados.
- Migraciones y cambios en el modelo de datos.
- Endpoints implementados con ejemplos de solicitudes y respuestas.
- Pruebas ejecutadas y sus resultados reales.
- Instrucciones para configurar las variables de entorno y ejecutar el proyecto.
- Limitaciones conocidas y tareas pendientes.

**Importante:** no marques una funcionalidad como terminada si solo se creó la interfaz o si los datos son simulados. La autenticación, la lista de deseos y sus operaciones deben estar conectadas al backend y a la base de datos reales.