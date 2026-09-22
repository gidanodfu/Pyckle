/*
 * Copyright (C) 2026 Josue David (gidanodfu)
 * https://github.com/gidanodfu
 *
 * This file is part of Pyckle.
 *
 * Pyckle is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as
 * published by the Free Software Foundation, either version 3 of
 * the License, or (at your option) any later version.
 *
 * Pyckle is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public License
 * along with Pyckle. If not, see <https://www.gnu.org/licenses/>.
 */

import { h } from "../../../components/dom.js";
import { routes, site } from "../../../lib/paths.js";
import { pending, internalLink, paragraph, bullets, legalSection, LegalShell } from "../layout.js";

export function LegalIndexPage() {
  return LegalShell({
    title: "Información legal",
    subtitle: "Documentos legales y de transparencia de Pyckle.",
    current: routes.legal,
    children: [
      legalSection(
        "Qué es Pyckle",
        paragraph(
          "Pyckle es un marketplace tecnológico que conecta a clientes que necesitan reparar dispositivos con técnicos independientes en Perú. La plataforma permite publicar solicitudes, recibir cotizaciones, acordar una reparación, dar seguimiento a la orden y comunicarse por chat.",
        ),
        paragraph(
          "Pyckle no presta directamente los servicios de reparación: los servicios son ofrecidos y ejecutados por técnicos independientes registrados en la plataforma.",
        ),
      ),
      legalSection(
        "Datos de la entidad responsable",
        paragraph(
          "Estos datos aún no están configurados en el proyecto y deben completarse antes de publicar una versión definitiva:",
        ),
        bullets([
          h("span", {}, "Razón social: ", pending(site.legalEntity)),
          h("span", {}, "RUC: ", pending(site.taxId)),
          h("span", {}, "Domicilio fiscal: ", pending(site.fiscalAddress)),
          h("span", {}, "Correo legal: ", pending(site.legalEmail)),
        ]),
      ),
      legalSection(
        "Documentos",
        bullets([
          h("span", {}, internalLink("Política de Privacidad", routes.privacy), ": qué datos recopila Pyckle y con qué finalidad."),
          h("span", {}, internalLink("Términos y Condiciones", routes.terms), ": reglas de uso de la plataforma."),
          h("span", {}, internalLink("Tratamiento de Datos Personales", routes.dataTreatment), ": detalle operativo del tratamiento de datos."),
          h("span", {}, internalLink("Contacto", routes.contact), ": canales de soporte y consultas legales."),
        ]),
      ),
      legalSection(
        "Alcance",
        paragraph(
          "Pyckle facilita la intermediación, la trazabilidad de las órdenes y la comunicación entre las partes. No es un taller de reparación, no emplea a los técnicos y no garantiza el resultado de los trabajos realizados fuera de la plataforma.",
        ),
      ),
    ],
  });
}
