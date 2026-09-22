# Conexión a PostgreSQL con DBeaver

Guía para inspeccionar la base de datos de Pyckle desde DBeaver. **No contiene
contraseñas**: las credenciales se leen del archivo `.env` local, que está
ignorado por Git.

## 1. Variables de configuración

La conexión se define con las variables del proyecto (`.env` / `.env.example`):

| Variable | Uso | Valor por defecto |
|----------|-----|-------------------|
| `POSTGRES_HOST` | Host de la base | `postgres` (dentro de Docker) |
| `POSTGRES_PORT` | Puerto publicado en el host | `5432` |
| `POSTGRES_DB` | Base de datos de la app | `pyckle` |
| `POSTGRES_USER` | Usuario de la base | `pyckle` |
| `POSTGRES_PASSWORD` | Contraseña (desde `.env`) | — |
| `TEST_DATABASE_URL` | Base de tests (`pyckle_test`) | derivada si falta |

`DATABASE_URL` es la URL que usa la aplicación dentro de Docker; para DBeaver
interesa `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER` y
`POSTGRES_PASSWORD`.

## 2. Desarrollo local

El `docker-compose.yml` de desarrollo publica PostgreSQL **solo en
`127.0.0.1`**. Los servicios también están en la red `edge`: Docker no publica
puertos de contenedores conectados únicamente a una red `internal`. En DBeaver
crea una conexión PostgreSQL con:

- **Host**: `127.0.0.1`
- **Port**: el valor de `POSTGRES_PORT` (por defecto `5432`)
- **Database**: `pyckle`
- **Username**: `POSTGRES_USER`
- **Password**: `POSTGRES_PASSWORD` del `.env` local
- **SSL**: desactivado (`sslmode=disable`)

Cadena JDBC de referencia (sin contraseña):

```
jdbc:postgresql://127.0.0.1:5432/pyckle
```

Para inspeccionar la base de tests usa la misma conexión cambiando la base a
`pyckle_test`. Evita consultar mientras corre la suite (los tests truncan tablas
de datos).

## 3. Producción

En producción PostgreSQL y Redis **no publican puertos**: solo viven en la red
interna de Docker. Para conectarte usa una de estas opciones:

1. **Túnel SSH** (recomendado):
   ```bash
   ssh -L 5433:127.0.0.1:5432 usuario@servidor
   ```
   y en DBeaver conecta a `127.0.0.1:5433` con las credenciales de producción.
2. **Administración dentro del servidor**:
   ```bash
   docker compose -f docker-compose.prod.yml exec postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"
   ```

No expongas el puerto `5432` a Internet. Si necesitas acceso remoto directo,
habilítalo solo con TLS (`sslmode=verify-full`), firewall y credenciales
robustas, y documenta el cambio.

## 4. Buenas prácticas

- No guardes contraseñas en DBeaver compartido, capturas, issues ni commits.
- Si una credencial se filtra, rótala en Supabase/PostgreSQL y actualiza el
  `.env` local y los secretos del servidor.
- Usa una conexión de solo lectura para explorar datos de producción.
