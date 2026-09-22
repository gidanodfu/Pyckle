// Aplica el tema antes del primer render para evitar destello.
// Script clásico (no módulo) para que el navegador lo ejecute de forma
// bloqueante antes de pintar; permite una CSP estricta sin 'unsafe-inline'.
(function () {
  try {
    var stored = localStorage.getItem("pyckle_theme");
    var dark = stored
      ? stored === "dark"
      : window.matchMedia("(prefers-color-scheme: dark)").matches;
    if (dark) document.documentElement.classList.add("dark");
  } catch (error) {
    // Sin almacenamiento disponible: se usa el tema claro por defecto.
  }
})();
