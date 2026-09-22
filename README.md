# Pyckle

Marketplace de reparación de dispositivos tecnológicos en Perú. Los clientes
publican solicitudes, los técnicos verificados envían cotizaciones y ambas
partes siguen la orden y conversan en tiempo real.

- **Backend**: FastAPI + SQLAlchemy 2 async + asyncpg + Alembic + PostgreSQL 16 + Redis.
- **Frontend**: HTML5 + Tailwind CSS v4 + JavaScript (ES Modules) + Vite + Lucide Icons. Sin frameworks.
- **Infra**: Docker Compose, Nginx como reverse proxy, PostgreSQL y Redis en red interna.
- **Almacenamiento**: Supabase Storage (S3 compatible) en producción; volumen local en desarrollo.
  Las imágenes se sirven siempre a través de Pyckle (`/api/v1/media/...`).

---

## 1. Arquitectura

**Backend**: un paquete por dominio con sus cuatro capas (`router.py`, `schemas.py`,
`service.py`, `repository.py`). Los modelos permanecen centralizados para no romper
relaciones ni Alembic.

```
backend/app/
  api/router.py   Ensambla los routers de dominio (HTTP y WebSocket)
  core/           Infraestructura transversal: config, security, dependencies,
                  exceptions, logging, paths, phone, ratelimit, redis, text
  db/             Base declarativa, sesión async con pool, seed, demo_data, ubigeo
  domains/        Un paquete por dominio: router + schemas + service + repository
                  (auth, users, technicians, geo, repair_requests, quotations,
                  orders, conversations, notifications, reviews, media, admin)
  infrastructure/ storage.py (local/S3) y repository.py (base + paginación)
  models/         Modelos SQLAlchemy (22 tablas, punto único de import para Alembic)
  schemas/        Schemas compartidos (common.py)
  permissions/    RBAC (require_permissions / require_roles)
  main.py         Aplicación FastAPI
frontend/src/
  api/            Cliente HTTP (client.js) + endpoints centralizados (endpoints.js)
  app/            bootstrap (monta shell y listeners), router (render + guardias),
                  routes (tabla de rutas) y session (auth, WS, notificaciones)
  components/     Globales: ui/ (primitives, feedback, data, overlay, busy),
                  layout/ (navbar, user-menu, notification-bell, container),
                  dom, icons, popover, geo, brand, footer, cards, tables
  domains/        Una carpeta por dominio con page.js + components/
  lib/            Utilidades transversales (paths, navigation, phone, guardia)
  services/       Auth y WebSocket
  state/          Estado global mínimo (store)
  styles/style.css
  main.js         Entrypoint: importa estilos y arranca `app/bootstrap.js`
infra/nginx/      Configuración Nginx (dev y prod)
```

**¿Dónde va cada cosa?**

| Necesidad | Ubicación |
|-----------|-----------|
| Nueva página/route | `frontend/src/domains/<dominio>/page.js` + ruta en `lib/paths.js` + tabla de `app/routes.js` |
| Componente usado por varios dominios | `frontend/src/components/` |
| Componente de un solo dominio | `frontend/src/domains/<dominio>/components/` |
| Nueva llamada API | builder en `frontend/src/api/endpoints.js`; los componentes nunca escriben `/api/...` |
| Nueva ruta SPA | `frontend/src/lib/paths.js` (los componentes consumen `routes.*`) |
| Navegación desde un dominio | `navigate()` de `frontend/src/lib/navigation.js` (navigator diferido, sin ciclos) |
| Asset (logo, favicon) | import en `frontend/src/lib/paths.js` (`assets.*`) |
| Nuevo endpoint | `backend/app/domains/<dominio>/router.py` y registrar en `app/api/router.py` |
| Nueva lógica de negocio | `backend/app/domains/<dominio>/service.py` (nunca en routers ni schemas) |
| Nueva consulta SQL | `backend/app/domains/<dominio>/repository.py` |
| Nuevo contrato de API | `backend/app/domains/<dominio>/schemas.py` |
| Panel admin | paquete `backend/app/domains/admin/` (un router por área + `stats.py` + `dependencies.py`) |
| Nuevo modelo/tabla | `backend/app/models/<dominio>.py` + import en `models/__init__.py` + migración Alembic |
| Infraestructura compartida | `backend/app/core/` (config, security, storage, Redis...) |
| Datos demo del seed | `backend/app/db/demo_data.py` (solo literales) |

Cada dominio mantiene las dependencias explícitas (`router → service →
repository → db`): los routers no importan repositories ni modelos y los services
no dependen de FastAPI (lo verifica `backend/tests/test_architecture.py`). En el
frontend, `app/` orquesta y `domains/` contiene las pantallas; el único entrypoint
es `main.js`.

### Router y App Shell (frontend)

- `#app` monta una sola vez el shell (`navbar` + `<main id="view">` + `footer`); las
  navegaciones solo reemplazan el contenido de `#view`.
- Cada `render()` captura una versión de navegación (`renderVersion`); solo el render
  vigente escribe en el DOM, por lo que una respuesta async antigua no puede
  sobrescribir una navegación posterior.
- `components/popover.js` centraliza los desplegables (notificaciones y menú de
  usuario): un único listener de documento, un solo panel abierto y sin
  `stopPropagation`.
- Los modales se registran en `components/ui/overlay.js` y se cierran
  automáticamente al navegar.
- `lib/navigation.js` expone el `navigate()` del router de forma diferida: los
  módulos de dominio navegan sin importar `app/router.js`, rompiendo el ciclo
  router ↔ páginas.
- El footer se posiciona por layout flex (`#app` flex column, `#view` flex: 1), sin
  `position: fixed` ni alturas mínimas arbitrarias.

El flujo de una petición es: `router -> service -> repository -> base de datos`.
Los routers nunca contienen SQL; los servicios nunca devuelven `Response`.

### Decisiones documentadas

- **Aceptar una cotización crea la orden automáticamente.** Al aceptar, la cotización
  pasa a `accepted`, las demás quedan `rejected`, la solicitud pasa a `accepted` con
  técnico asignado, se crea la `order` (estado `pending`), su primer registro de
  historial y la `conversation` entre cliente y técnico.
- **Tablas adicionales al listado inicial**: `role_permissions` (unión rol-permiso),
  `specialties` (catálogo; `technician_specialties` es la unión técnico-especialidad)
  y `departments` / `provinces` / `districts` (ubigeo del Perú).
- **Almacenamiento configurable**: `STORAGE_BACKEND=local` (volumen Docker, desarrollo)
  o `s3` (Supabase Storage, producción). La base de datos guarda solo `storage_key`;
  la URL pública se construye de forma centralizada en `app/core/paths.py`.
- **Redis** se usa para revocación/rotación de refresh tokens, rate limit de login y
  fan-out de WebSockets entre workers (pub/sub).
- **Modalidad de atención del técnico**: `offers_home_service` y
  `offers_workshop_service`; debe existir al menos una (domicilio, local o ambas).
  Si atiende en taller, `workshop_address` es obligatoria; si no, se normaliza a
  `null`. La regla vive en `app/domains/technicians/modality.py` y valida tanto el
  registro como el estado final de un PATCH (perfil actual + cambios).
- **RareUI no se integra**: es una librería de componentes React/Next.js con Framer
  Motion y este frontend es vanilla JS + Tailwind. Se mantiene un único sistema de
  diseño propio con Lucide Icons para no mezclar estéticas ni reescribir el SPA.

---

## 2. Requisitos

- Docker Engine 24+ y Docker Compose v2.
- GNU Make (opcional; se incluye `./dev` como alternativa sin Make).
- Cuenta de Supabase con un bucket de Storage (solo para producción).
- Dominio o subdominio gestionado en Cloudflare (solo para producción).

---

## 3. Puesta en marcha (desarrollo)

```bash
cp .env.example .env
# Edita .env: SECRET_KEY, contraseñas de Postgres, ADMIN_PASSWORD y DEMO_PASSWORD.
# Genera la clave con: openssl rand -hex 32

make up          # o: ./dev up
make migrate     # aplica migraciones Alembic
make seed        # roles, permisos, especialidades, ubigeo completo, admin y demo
```

Servicios disponibles:

| Servicio  | URL                          | Notas                                  |
|-----------|------------------------------|----------------------------------------|
| Frontend  | http://localhost             | vía Nginx (Vite HMR en :5173)          |
| Backend   | http://localhost/api/v1      | vía Nginx (directo en :8000)           |
| Docs API  | http://localhost:8000/docs   | OpenAPI/Swagger                        |
| Postgres  | 127.0.0.1:5432               | solo acceso local                      |
| Redis     | 127.0.0.1:6379               | sin exposición pública                 |

Datos demo (con `SEED_DEMO_DATA=true` y `DEMO_PASSWORD`):

- 12 clientes `demo.customer.NNN@pyckle.dev` y 12 técnicos
  `demo.technician.NNN@pyckle.dev` (6 verificados y 6 no verificados),
  distribuidos en 9 departamentos, con las 7 especialidades, órdenes completadas
  con reseñas reales y solicitudes abiertas con cotizaciones pendientes.
- Usuarios base de compatibilidad: `cliente@pyckle.dev` y `tecnico@pyckle.dev`.
- Todos usan la contraseña `DEMO_PASSWORD`. El demo es **idempotente**: ejecutar
  `make seed` varias veces no duplica datos.
- Admin: `ADMIN_EMAIL` / `ADMIN_PASSWORD` (solo crea la cuenta administradora;
  ver la aclaración en la sección de variables de entorno).

Conexión de base de datos con DBeaver:
[docs/development/dbeaver.md](docs/development/dbeaver.md).

---

## 4. Comandos

| Comando           | Descripción                                        |
|-------------------|----------------------------------------------------|
| `make up`         | Levanta el stack de desarrollo (build incluido)    |
| `make down`       | Detiene el stack (conserva volúmenes)              |
| `make migrate`    | Aplica migraciones hasta `head`                    |
| `make revision m="descripción"` | Crea una migración autogenerada      |
| `make downgrade`  | Revierte la última migración                       |
| `make seed`       | Carga datos semilla (incluye todo el ubigeo)       |
| `make test`       | Ejecuta la suite de tests                          |
| `make lint`       | Ruff check + format check                          |
| `make logs`       | Logs en vivo                                       |
| `make shell` / `make db-shell` / `make redis-cli` | Utilidades          |
| `make prod-up`    | Levanta producción (`docker-compose.prod.yml`)     |
| `make clean`      | Borra contenedores y volúmenes (destructivo)       |

Sin Make, usa el wrapper equivalente: `./dev up`, `./dev migrate`, `./dev test`, etc.

---

## 5. Migraciones y datos geográficos

```bash
make migrate
# o directamente:
docker compose exec -T backend alembic upgrade head
docker compose exec -T backend alembic downgrade -1
```

La migración `3715a0d52953` agrega:

- Tablas `departments`, `provinces`, `districts` (código ubigeo único + jerarquía).
- `users.phone_normalized` (canónico `+51XXXXXXXXX`, único) con backfill de teléfonos existentes.
- `customer_profiles`, `technicians` y `repair_requests` con `department_id`/`province_id`/`district_id`.
- `conversations.status` (`open`/`closed`/`archived`) y `closed_at`.
- Eliminación de `repair_request_images.url` (solo se guarda `storage_key`).
- Índices compuestos para órdenes, notificaciones y reseñas.

El seed carga el ubigeo completo (25 departamentos, 196 provincias, 1874 distritos)
desde `backend/app/db/data/ubigeo_peru.json` de forma **idempotente**, por lo que
`python -m app.db.seed` puede ejecutarse varias veces sin duplicar datos.

---

## 6. Variables de entorno

Todas se declaran en `.env.example`. Las principales:

| Variable | Descripción |
|----------|-------------|
| `APP_NAME` | Nombre visible de la aplicación (`Pyckle`) |
| `SECRET_KEY` | Clave de firma JWT (obligatoria, `openssl rand -hex 32`) |
| `DATABASE_URL` | URL async de PostgreSQL (`postgresql+asyncpg://...`) |
| `TEST_DATABASE_URL` | Base de tests; si se omite se deriva `<DB>_test` |
| `DB_POOL_SIZE` / `DB_MAX_OVERFLOW` / `DB_POOL_TIMEOUT` / `DB_POOL_RECYCLE` | Pool de conexiones |
| `LOGIN_MAX_ATTEMPTS` / `LOGIN_BLOCK_SECONDS` | Rate limit de login (por defecto 3 / 300 s) |
| `REGISTER_MAX_PER_IP` / `REGISTER_WINDOW_SECONDS` | Rate limit de registro por IP (por defecto 20 / 3600 s) |
| `REDIS_URL` | URL de Redis (`/0` app; los tests usan `/15`) |
| `CORS_ORIGINS` / `TRUSTED_HOSTS` / `FRONTEND_URL` | Seguridad HTTP |
| `STORAGE_BACKEND` | `local` o `s3`; **obligatorio `s3` en producción** (el almacenamiento local no es válido para múltiples instancias) |
| `SUPABASE_S3_*` | Endpoint, región, credenciales y bucket de Supabase |
| `MAX_UPLOAD_SIZE_MB` / `MAX_IMAGES_PER_REQUEST` / `ALLOWED_IMAGE_TYPES` | Límites de subida |
| `ADMIN_EMAIL` / `ADMIN_PASSWORD` | Cuenta administradora creada por el seed |
| `DOMAIN` | Dominio público para Nginx en producción |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` / `GOOGLE_REDIRECT_URI` | OAuth con Google (solo backend). Vacíos deshabilitan el proveedor |

**Pool**: el máximo de conexiones es `workers × (DB_POOL_SIZE + DB_MAX_OVERFLOW)`.
Los valores por defecto (5 + 10) y 2 workers dan 30 conexiones máximas.

**Sobre `ADMIN_EMAIL`**: es la configuración central del correo de la cuenta
administradora que crea `seed_admin` (`settings.admin_email`); no es lo mismo que
la cuenta admin existente en la base (que puede editarse desde `/admin/users`) ni
que los correos de contacto legales, que hoy son placeholders en
`frontend/src/lib/paths.js`. Cambiar `ADMIN_EMAIL` no renombra una cuenta ya
creada: solo define el correo con el que se crea si aún no existe.

**Nunca subas `.env` a Git.** `.gitignore` ya excluye `.env` y `.env.*`
(excepto `.env.example`, que solo contiene placeholders).

---

## 7. API REST y WebSockets

API versionada bajo `/api/v1`:

`/auth`, `/users`, `/geo`, `/media`, `/specialties`, `/technicians`,
`/repair-requests`, `/quotations`, `/orders`, `/conversations`, `/reviews`,
`/notifications`, `/admin`.

Documentación OpenAPI interactiva en `/docs` (y `/redoc`), **disponible solo en
desarrollo**; en producción se deshabilitan las rutas de docs/OpenAPI. Todas las
respuestas de error son consistentes: `{"detail": "...", "code": "...", "details": ...}`.

WebSockets:

| Endpoint | Uso |
|----------|-----|
| `POST /api/v1/ws/ticket` | Emite un ticket efímero de un solo uso (autenticado por Bearer) |
| `/ws/notifications?ticket=<ticket>` | Notificaciones en tiempo real |
| `/ws/chat/{conversation_id}?ticket=<ticket>` | Chat cliente-técnico (recepción; el envío también funciona por REST) |

El JWT no viaja en la URL: el cliente pide un ticket por REST, lo usa una vez y el
servidor lo consume de forma atómica (Redis `GETDEL`, TTL 60 s).

### Endpoints destacados de la última iteración

- `GET /geo/departments`, `GET /geo/departments/{id}/provinces`, `GET /geo/provinces/{id}/districts`.
- `GET /api/v1/media/{storage_key}`: sirve la imagen desde el backend de almacenamiento
  activo. Exige un enlace firmado (`?e=<exp>&s=<hmac>`) de corta duración; no es
  accesible conociendo solo `storage_key`.
- `GET /orders/{id}/customer-profile`: perfil público del cliente para el técnico asignado.
- `GET /technicians` acepta filtros de zona y devuelve `scope`/`expanded`.
- `GET /repair-requests/available` filtra por la zona del técnico y devuelve `scope`/`expanded`.
- `POST /notifications/read-all` es idempotente y devuelve `{updated, unread}`.

### Ciclo de reparación (gestión técnica)

Una vez aceptada una cotización se crea la orden (la reparación) en estado
técnico `awaiting_receipt`. El técnico asignado gestiona el proceso:

- `PATCH /orders/{id}/status`: transiciones técnicas no terminales
  (`received`, `diagnosis`, `waiting_customer`, `waiting_part`, `in_repair`,
  `testing`, `ready`).
- `PUT /orders/{id}/repair-details`: diagnóstico, trabajo realizado y pruebas.
- `POST /orders/{id}/complete` | `/not-repairable` | `/cancel`: cierre con
  resultado (`repaired`/`not_repairable`/`cancelled`) y **generación obligatoria
  del informe**.
- `GET/POST /orders/{id}/price-changes` y `.../{change_id}/approve|reject`:
  aumentos requieren aprobación del cliente; las bajadas se registran y notifican.
- `GET/POST /orders/{id}/costs`: costos internos vs. visibles al cliente.
- `GET /orders/{id}/report` (PDF autenticado) y `GET /orders/{id}/reports`.
- `GET /orders` acepta `status`, `result`, `specialty_id`, `from_date`, `to_date`.
- `GET /technicians/me/summary`: agregados por estado y categoría.

Panel del técnico: `/technician` (resumen), `/technician/repairs`,
`/technician/quotations`, `/technician/reports`.

---

## 8. Reglas de negocio y seguridad

### Teléfonos

Se normalizan a `+51XXXXXXXXX` (celular peruano de 9 dígitos) antes de comparar y
guardar. `999123456`, `999 123 456`, `+51 999 123 456` y `0051...` se consideran el
mismo número. `users.phone_normalized` tiene índice único; duplicados en cualquier
formato se rechazan.

### Rate limit de login

Hasta 3 intentos fallidos; al tercero se bloquea 300 segundos. El bloqueo se guarda
en Redis con TTL (`login:attempts:*`, `login:blocked:*`) usando un hash de
`email + IP`, y aplica incluso con credenciales correctas. Todas las respuestas de
credenciales son genéricas ("Credenciales incorrectas.") y el bloqueo responde 429.

### Rate limit de registro

El alta de cuentas (`POST /auth/register` y `POST /auth/oauth/complete`) reserva
un intento **por IP confiable** antes de hashear con Argon2: hasta
`REGISTER_MAX_PER_IP` altas por ventana de `REGISTER_WINDOW_SECONDS` (20 por hora
por defecto). El principal es la IP y no el email porque variar el email en cada
intento es trivial; la IP es lo que acota el abuso (Argon2 y escrituras). La
reserva es atómica (`INCR` + `EXPIRE NX`) y reutiliza el mismo mecanismo que el
login. Es **independiente** del TTL de onboarding OAuth (`oauth:onboarding:*`,
120 s, un solo uso), que solo acota la ventana para completar un registro ya
iniciado con Google.

La aplicación protege el origin; Cloudflare puede añadir una capa adicional en
el edge, pero ninguna garantía depende exclusivamente de él. Si Redis no está
disponible, la reserva falla cerrada y responde 503 (mismo criterio que el
resto de mecanismos con estado en Redis).

### Sesiones, XSS y CSP

Los tokens de sesión viven hoy en `localStorage` (`pyckle_access_token`,
`pyckle_refresh_token`), por lo que un XSS podría exfiltrar la sesión. Como
mitigación se aplica una **Content-Security-Policy** en `nginx.prod.conf`
(primero en modo `Report-Only`): `script-src 'self'`, `style-src 'self'`, sin
`unsafe-inline` ni `unsafe-eval`. El arranque del tema vive en
`frontend/public/theme-init.js` (script externo) y no hay estilos ni scripts
inline. La migración de la sesión a cookie `HttpOnly` + protección CSRF queda
para una fase dedicada (afecta a OAuth, WebSockets y multi-pestaña).

Al cambiar la contraseña se incrementa `users.token_version`: los JWT llevan el
claim `tv` y un token emitido antes del cambio se rechaza de inmediato (access y
refresh), sin consultas adicionales por petición.

### Ubicación, zonas y privacidad

- Clientes y técnicos eligen departamento → provincia → distrito (validado en backend).
- La ubicación se puede actualizar desde el perfil; las reparaciones ya realizadas
  conservan su ubicación histórica.
- La búsqueda de técnicos y las solicitudes disponibles se filtran por zona con
  fallback distrito → provincia → departamento, indicado con `scope`/`expanded`.
- El técnico con taller debe registrar la dirección del local; si no ofrece taller,
  no se exige.
- La dirección exacta del cliente es privada: solo la ve el dueño, un administrador
  o el técnico asignado tras aceptar la cotización. No aparece en perfiles públicos.
- El perfil público del cliente muestra nombre, fecha de unión, reparaciones
  completadas y ubicación general.

### Marco legal y aceptación de Términos

- El registro (cliente y técnico) exige aceptar los Términos y Condiciones. La
  aceptación se valida en el frontend y en el backend (`accept_terms` obligatorio)
  y se persiste en `users.terms_accepted_at`.
- Páginas públicas: `/legal`, `/legal/privacy`, `/legal/terms`,
  `/legal/data-treatment` y `/contact`, enlazadas desde el footer.
- Los textos son un **borrador informativo** compatible con la Ley N.º 29733
  (Perú); no constituyen asesoría legal y están pendientes de revisión. Los datos
  de la entidad (razón social, RUC, domicilio, correos) figuran como placeholders
  en `frontend/src/lib/paths.js` y deben configurarse antes de publicar.

### Logo e identidad

- El recurso oficial vive en `frontend/assets/img/Icono/`. Vite lo procesa y los
  componentes lo consumen desde `frontend/src/lib/paths.js` (`assets.logo`); no se
  escriben rutas de assets a mano. Los derivados optimizados (`Pyckle-256/180/64`)
  y el favicon se generan a partir del original sin modificarlo.

### Imágenes

- Validación por MIME, extensión, bytes mágicos, tamaño y cantidad; nombres y
  paths generados por el servidor (sin path traversal).
- La base de datos guarda `storage_key` (por ejemplo
  `requests/{request_id}/{uuid}.png`) y sirve la imagen por
  `GET /api/v1/media/{storage_key}?e=<exp>&s=<hmac>`, igual en desarrollo y
  producción, sin URLs de Supabase hardcodeadas ni depender de que el bucket sea
  público. La URL va firmada (HMAC con `SECRET_KEY`, TTL 300 s) y se responde con
  `Cache-Control: private`, por lo que una imagen privada no queda accesible solo
  con conocer su clave ni se cachea como pública.
  - Riesgo aceptado: la firma depende de `storage_key + exp`, no del usuario, así
    que una URL firmada es un bearer de corta duración (300 s) que quien la posea
    puede reutilizar dentro del TTL. Se genera solo a espectadores autorizados
    (dueño, técnico asignado o admin) y no es enumerable. Ligarla al usuario
    exigiría que `<img>` autentique, lo que depende de la futura migración de la
    sesión a cookie.

### Chats

Estados `open` → `archived` (el enum también contempla `closed`). Al completar o
cancelar la orden, la conversación se archiva con `closed_at`: deja de aceptar
mensajes (REST y WebSocket) y permanece visible en "Archivados" con todo el historial.

---

### Inicio de sesión con Google (OAuth 2.0 server-side)

El frontend **no implementa OAuth 2.0 directamente**. FastAPI actúa como cliente
OAuth confidencial y mantiene las credenciales y el intercambio de tokens
exclusivamente en servidor:

```
Frontend ──GET /api/v1/auth/google──► FastAPI ──► Google (login/consent)
                                              │
                    Google ──code+state──► /api/v1/auth/google/callback
                                              │
                                   valida identidad (iss/aud/nonce/PKCE)
                                              │
                                   users / oauth_accounts (PostgreSQL)
                                              │
                                   sesión Pyckle (JWT) ──► Frontend
```

- El frontend solo conoce el endpoint de Pyckle (`/api/v1/auth/google`); navega
  a él y espera. Nunca ve `client_secret`, tokens de Google ni el callback.
- El backend valida la identidad, busca/crea el usuario local y emite la sesión
  normal de Pyckle. Tras el callback entrega un código de intercambio de un solo
  uso (Redis, TTL corto) que el frontend canjea por el `TokenPair` habitual.
- Configura en Google Cloud el **Authorized redirect URI** igual a
  `GOOGLE_REDIRECT_URI` (en desarrollo:
  `http://localhost:8000/api/v1/auth/google/callback`).
- `GET /api/v1/auth/providers` indica si el proveedor está habilitado; si no,
  el botón no se muestra y `/auth/google` responde 404.
- Política de cuentas: un usuario nuevo pasa por el formulario de registro
  (onboarding) antes de crear la cuenta; un email ya existente **no** se vincula
  automáticamente; el rol admin no puede usar Google. La tabla
  `oauth_accounts` es genérica (`provider` + `provider_user_id`), lista para
  añadir más proveedores sin tocar `User`.

---

## 9. Tests y calidad

```bash
make test    # pytest
make lint    # Ruff
```

Los tests usan una base `pyckle_test` (creada o derivada automáticamente) y la base
lógica 15 de Redis, por lo que nunca tocan los datos de la aplicación. Cubren:
autenticación y rate limit, teléfonos, ubicaciones, privacidad de direcciones, zonas,
chat, cotizaciones con reseñas, perfiles, modalidad de atención del técnico,
notificaciones, imágenes/media, Unicode, arquitectura por dominios y un flujo
end-to-end completo.

Frontend:

```bash
cd frontend && npm run build   # build de producción
npm test                       # tests unitarios (teléfono, guardia de navegación)
npm run test:dom               # build + tests DOM (shell, carreras, popovers, modales, rutas, modalidad, arquitectura)
```

`test:dom` usa `happy-dom` (devDependency) y valida en Node el shell persistente,
la carrera de renders (una navegación lenta no sobrescribe la vigente), el gestor de
popovers, el cierre de modales, el render de todas las rutas y el formulario de
modalidad. El layout visual también se verificó con Chromium real en
desktop/tablet/móvil durante el desarrollo.

---

## 10. Despliegue en VPS Ubuntu con Cloudflare

### 10.1 Preparar el VPS

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker "$USER"
# Cierra sesión y vuelve a entrar
git clone <tu-repositorio> pyckle
cd pyckle
cp .env.example .env
```

Ajusta como mínimo:

```env
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=<openssl rand -hex 32>
POSTGRES_PASSWORD=<password fuerte>
DATABASE_URL=postgresql+asyncpg://pyckle:<password>@postgres:5432/pyckle
CORS_ORIGINS=https://fix.tudominio.com
TRUSTED_HOSTS=fix.tudominio.com
FRONTEND_URL=https://fix.tudominio.com
DOMAIN=fix.tudominio.com
STORAGE_BACKEND=s3
SUPABASE_S3_ENDPOINT=https://<project-ref>.storage.supabase.co/storage/v1/s3
SUPABASE_S3_REGION=<region>
SUPABASE_S3_ACCESS_KEY_ID=<access-key>
SUPABASE_S3_SECRET_ACCESS_KEY=<secret-key>
SUPABASE_S3_BUCKET=pyckle
ADMIN_EMAIL=admin@tudominio.com
ADMIN_PASSWORD=<password fuerte>
SEED_DEMO_DATA=false
```

Crea el bucket en Supabase y genera credenciales S3
(Supabase > Project Settings > Storage > S3 access keys). Con el bucket privado es
suficiente: Pyckle sirve las imágenes a través de su API.

> **Migración desde la versión anterior (`pyckle-fix`)**: el proyecto Compose pasó
> de `pyckle-fix` a `pyckle`, por lo que Docker crea volúmenes nuevos. Para conservar
> los datos existentes:
>
> ```bash
> docker compose down
> for v in postgres_data redis_data media_data; do
>   docker volume create "pyckle_$v"
>   docker run --rm -v "pyckle-fix_$v:/from" -v "pyckle_$v:/to" alpine \
>     sh -c "cd /from && cp -a . /to/"
> done
> docker compose -f docker-compose.prod.yml up -d --build
> ```

### 10.2 DNS en Cloudflare

1. **DNS > Records**: registro **A** con el nombre deseado apuntando a la IP del VPS,
   Proxy status **Proxied**.
2. **SSL/TLS**: modo **Full (strict)**.
3. **SSL/TLS > Origin Server**: genera un Origin Certificate y guárdalo en
   `infra/certs/origin.crt` y `infra/certs/origin.key` (`chmod 600`).

`infra/certs/` está en `.gitignore`. Nginx los monta en `/etc/nginx/certs`.

### 10.3 Levantar producción

```bash
# 1) Migraciones: paso explícito y único antes de arrancar/escalar (nunca en
#    el comando de cada réplica, para no ejecutar DDL concurrente).
docker compose -f docker-compose.prod.yml run --rm backend alembic upgrade head
# 2) Arranque (escalable; Nginx reparte entre las réplicas)
docker compose -f docker-compose.prod.yml up -d --scale backend=2
make prod-logs
docker compose -f docker-compose.prod.yml exec -T backend python -m app.db.seed
```

Las migraciones se ejecutan una sola vez como paso previo; el backend no corre
`alembic upgrade head` en el arranque de cada réplica. Postgres y Redis **no**
publican puertos; Nginx aplica HSTS y cabeceras de seguridad.

### 10.4 Verificación

```bash
curl -fsS https://fix.tudominio.com/api/v1/health
curl -fsS https://fix.tudominio.com/ | head
```

### 10.5 Escalado horizontal

Nginx re-resuelve `backend` con el DNS embebido de Docker (`resolver 127.0.0.11`)
y reparte en round-robin, así que basta escalar el servicio (en producción el
backend no publica puertos):

```bash
docker compose -f docker-compose.prod.yml run --rm backend alembic upgrade head
docker compose -f docker-compose.prod.yml up -d --scale backend=3
```

Todas las réplicas comparten PostgreSQL, Redis y el mismo bucket S3
(`STORAGE_BACKEND=s3` es obligatorio en producción).

**Capacidad de conexiones a PostgreSQL**: cada worker abre hasta
`pool_size + max_overflow = 5 + 10 = 15` conexiones; con 2 workers por contenedor
cada instancia usa hasta **30**. Con `max_connections=100` (valor por defecto de
PostgreSQL) el máximo recomendado es **3 instancias** (90 conexiones); para más
réplicas, ajusta el pool o usa un pooler externo.

---

## 11. Estructura del repositorio

```
.
├── backend/          API FastAPI, migraciones, ubigeo, tests
├── frontend/         SPA Vite + Tailwind + Lucide
├── infra/nginx/      nginx.dev.conf y nginx.prod.conf
├── docker-compose.yml / docker-compose.prod.yml
├── Makefile / dev    Atajos de operación
├── .env.example      Plantilla de variables (sin secretos)
└── README.md
```

---

## License

Pyckle is free software licensed under the
[GNU Affero General Public License v3.0](LICENSE).

Copyright (C) 2026 Josue David (gidanodfu).

Author: [Josue David](https://github.com/gidanodfu)
