# Pyckle E2E (QA de navegador)

Harness de QA con Playwright + Chromium. Es **independiente** del build de la
app (su `package.json` no forma parte de `frontend/`, por lo que no afecta al
`npm ci` de la imagen Docker).

## Requisitos

- Stack de Pyckle levantado (`make up`) y seed aplicado (`make seed`).
- Node 20+.

## Instalación

```bash
cd e2e
npm install
npx playwright install chromium
```

## Uso

```bash
# Matriz de rutas x 6 viewports (dark, default)
QA_DEMO_PASSWORD=... QA_ADMIN_PASSWORD=... \
QA_REQUEST_ID=<uuid> QA_ORDER_ID=<uuid> QA_TECH_ID=<uuid> \
npm run qa

# Light mode
npm run qa:light

# Subconjunto de viewports
QA_VIEWPORTS=375x812,1440x900 npm run qa

# Interacciones y accesibilidad (menu, modal, tema, toast)
QA_DEMO_PASSWORD=... QA_ADMIN_PASSWORD=... npm run interactions
```

Variables: `QA_BASE` (por defecto `http://localhost`), `QA_THEME` (`dark`/`light`),
`QA_LABEL` (carpeta de salida), `QA_OUT`, `QA_SHOTS=0` para omitir capturas.

Salida en `e2e/artifacts/<label>/report.json` y screenshots por viewport.
El script devuelve código != 0 si hay hallazgos (errores de consola, pageerrors,
fallos de red, HTTP >=400, overflow horizontal, iconos faltantes).

Las credenciales llegan por variables de entorno y nunca se imprimen. No
incluir `.env` ni tokens en capturas.

## Datos de prueba

`interactions.mjs` comprueba el toast marcando notificaciones; requiere que el
usuario `QA_NOTIF_EMAIL` (por defecto `demo.customer.003@pyckle.dev`) tenga al
menos una notificación sin leer. Genera una con una acción real (por ejemplo,
que un técnico cambie el estado de una orden) antes de ejecutarlo.
