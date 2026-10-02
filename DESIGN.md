# Pyckle - Dirección de diseño

## Identidad
Marketplace de reparación que conecta clientes con técnicos. Herramienta de
trabajo real, técnica y sobria. La marca es Pyckle (logo e identidad propios);
el acento es azul claro. No se copia ninguna plantilla: se adopta una disciplina
visual de dashboard técnico y se aplica a todo el producto.

## Principio
El sistema manda, no la página. El orden de construcción es siempre:

```
Design System -> Layout -> Componentes -> Páginas -> Contenido
```

Ninguna página define colores, radios o spacing propios. Si un patrón se repite,
vive en un componente del sistema.

## Personalidad
Técnica, compacta, discreta y profesional. Dark-first. Alta densidad de
información sin desorden. Se evita: gradientes como recurso principal,
glassmorphism, sombras grandes, cards gigantes, exceso de pills, elementos
flotantes sin función, colores saturados y animaciones decorativas.

## Tema
**Dark es el tema por defecto y el más trabajado.** El usuario puede cambiar a
light con el toggle; la preferencia se guarda en `localStorage` y se restaura
antes del primer render (`public/theme-init.js`). La preferencia del sistema
solo aplica si el proyecto decide usarla como fallback; hoy el default es dark.

Ambos temas usan **los mismos tokens semánticos**; light no es otra aplicación,
es el mismo sistema sobre superficie clara. Ningún componente puede quedar con
colores de la paleta anterior.

## Paleta (tokens semánticos)
Se declaran en `frontend/src/styles/style.css` y se consumen como utilidades
Tailwind (`bg-surface`, `border-border`, `text-foreground`, `bg-primary`...).
Prohibido escribir un color literal en un componente si existe un token.

Dark (base):

| Token | Valor |
|-------|-------|
| `background` | `#0B1018` |
| `surface` | `#111823` |
| `surface-elevated` | `#161F2C` |
| `surface-hover` | `#1B2635` |
| `surface-strong` | `#23303F` |
| `border` | `#263241` |
| `border-subtle` | `#1D2733` |
| `foreground` | `#E7ECF2` |
| `foreground-secondary` | `#B5C0CC` |
| `muted` | `#7F8B99` |
| `primary` | `#6EA8FE` |
| `primary-hover` | `#82B5FF` |
| `primary-foreground` | `#08111F` |
| `success` | `#43C995` |
| `warning` | `#E5B85C` |
| `danger` | `#D96B7B` |
| `info` | `#6EA8FE` |

Light (mismos nombres, valores adaptados): `background #F6F8FB`, `surface
#FFFFFF`, `surface-elevated #FFFFFF`, `surface-hover #F1F5F9`, `border #E2E8F0`,
`foreground #0F172A`, `foreground-secondary #334155`, `muted #5B6675`, `primary
#2563EB`, `primary-foreground #FFFFFF`, `success #157F5B`, `warning #9A6B14`,
`danger #C23B4E`.

Reglas: sin negro `#000` ni blanco `#FFF` como fondo/texto general; semánticos
reconocibles; el acento solo con función.

## Geometría (radios)
```
sm    8px    inputs, botones, chips
md   10px    controles y contenedores compactos
lg   12px    cards y paneles
xl   16px    modales y superficies grandes
pill 9999px  badges y avatares
```
No usar `rounded-2xl`/`rounded-3xl` indiscriminadamente.

## Bordes y sombras
- Bordes `1px solid` con `--border` / `--border-subtle` como separadores
  principales. Las superficies deben distinguirse por color y borde, no por
  sombra.
- Sombras mínimas: solo superficies flotantes (dropdown, modal, toast) pueden
  usar una sombra sutil. Una card no lleva sombra.

## Spacing
Escala única: `4 / 8 / 12 / 16 / 20 / 24 / 32 / 40 / 48` (px). Se usan los
equivalentes de Tailwind (`1 / 2 / 3 / 4 / 5 / 6 / 8 / 10 / 12`). Container
`p-6`; card `p-4`; separación entre secciones `mt-6`/`mt-8`.

## Tipografía
Pila del sistema `-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif`.
Compacta y técnica, sin fuentes decorativas.

| Rol | Tamaño | Peso |
|-----|--------|------|
| Título de página | 24px (`text-2xl`) | semibold |
| Título de sección | 18px (`text-lg`) | semibold |
| Heading de card | 16px (`text-base`) | semibold |
| Body | 14px (`text-sm`) | normal |
| Texto secundario | 14px (`text-sm`) | normal, color `foreground-secondary` |
| Metadata | 12px (`text-xs`) | normal, color `muted` |
| Labels de formulario | 13-14px | medium |
| Badges | 11-12px | semibold |
| Métricas | 24-30px | semibold, `tabular-nums` |

## Iconografía
Solo Lucide para iconos funcionales. Tamaños `16 / 18 / 20 / 24` según
contexto. Sin emojis como sustitutos de iconos. Iconos con función, no
decoración.

## Estados
Toda vista de datos define loading, empty y error (y forbidden/not-found cuando
aplique). El color nunca es el único indicador: siempre acompaña texto o icono.
Todo componente define normal, hover, focus-visible, active, disabled y
loading/selected cuando corresponda, **en ambos temas**.

## Movimiento
Discreto y funcional: feedback de interacción y transición de estado. Sin
animaciones decorativas ni bucles. Respeta `prefers-reduced-motion`.

## Diales
Dial: ENERGY 2 / RHYTHM 1 / MOTION 1
