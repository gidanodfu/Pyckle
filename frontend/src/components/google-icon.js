const SVG_NS = "http://www.w3.org/2000/svg";

// "G" oficial de Google (multicolor). Único origen para Login y Registro.
const PATHS = [
  {
    fill: "#4285F4",
    d: "M43.611 20.083H42V20H24v8h11.303c-.792 2.237-2.231 4.166-4.087 5.571l.003-.002 6.19 5.238C36.971 39.205 44 34 44 24c0-1.341-.138-2.65-.389-3.917z",
  },
  {
    fill: "#34A853",
    d: "M24 44c5.166 0 9.86-1.977 13.409-5.192l-6.19-5.238C29.211 35.091 26.715 36 24 36c-5.202 0-9.619-3.317-11.283-7.946l-6.522 5.025C9.505 39.556 16.227 44 24 44z",
  },
  {
    fill: "#FBBC05",
    d: "M12.717 28.054A11.86 11.86 0 0 1 12 24c0-1.408.247-2.759.694-4.017l-.013.021-6.522-5.025A19.9 19.9 0 0 0 4 24c0 3.196.769 6.21 2.133 8.887l6.584-4.833z",
  },
  {
    fill: "#EA4335",
    d: "M24 12c2.94 0 5.598 1.01 7.68 2.68l5.564-5.564C33.988 5.996 29.31 4 24 4 16.318 4 9.701 8.337 6.306 14.691l6.571 4.819C14.655 15.108 18.961 12 24 12z",
  },
];

/** Icono "G" de Google, reutilizable y sin dependencias externas. */
export function googleIcon({ size = 18, class: extra = "" } = {}) {
  const svg = document.createElementNS(SVG_NS, "svg");
  svg.setAttribute("viewBox", "0 0 48 48");
  svg.setAttribute("width", String(size));
  svg.setAttribute("height", String(size));
  svg.setAttribute("aria-hidden", "true");
  svg.setAttribute("class", `shrink-0 ${extra}`.trim());
  for (const path of PATHS) {
    const node = document.createElementNS(SVG_NS, "path");
    node.setAttribute("fill", path.fill);
    node.setAttribute("d", path.d);
    svg.append(node);
  }
  return svg;
}
