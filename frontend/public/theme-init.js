// Aplica el tema antes del primer render para evitar destello.
// Script clásico (no módulo) para que el navegador lo ejecute de forma
// bloqueante antes de pintar; permite una CSP estricta sin 'unsafe-inline'.
// Dark es el tema por defecto de Pyckle. La preferencia guardada manda; si no
// hay almacenamiento disponible se usa la preferencia del sistema como fallback.
(function () {
  var dark = true;
  try {
    var stored = localStorage.getItem("pyckle_theme");
    if (stored) dark = stored === "dark";
  } catch (error) {
    dark = window.matchMedia("(prefers-color-scheme: dark)").matches;
  }
  if (dark) document.documentElement.classList.add("dark");
})();
