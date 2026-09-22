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
import { pending, internalLink, paragraph, bullets, legalSection, LegalShell, PENDING_RESPONSE } from "../layout.js";

export function ContactPage() {
  return LegalShell({
    title: "Contacto",
    subtitle: "Canales de atención de Pyckle.",
    current: routes.contact,
    children: [
      legalSection(
        "Información general",
        paragraph(
          "Pyckle es un marketplace de reparación de dispositivos en Perú. Por ahora la atención se realiza por correo electrónico; no existe un formulario de contacto en línea ni atención telefónica.",
        ),
      ),
      legalSection(
        "Motivos de contacto",
        bullets([
          h("span", {}, h("b", {}, "Soporte de cuenta y solicitudes: "), pending(site.contactEmail), ". Problemas de acceso, incidencias con solicitudes, cotizaciones, órdenes o chat."),
          h("span", {}, h("b", {}, "Consultas legales: "), pending(site.legalEmail), ". Dudas sobre los Términos y Condiciones o el uso de la plataforma."),
          h("span", {}, h("b", {}, "Privacidad y datos personales: "), pending(site.privacyEmail), ". Ejercicio de derechos ARCO, revocación de consentimiento y consultas de privacidad."),
        ]),
      ),
      legalSection(
        "Antes de escribirnos",
        paragraph(
          "Incluye tu nombre completo y el correo con el que te registraste para que podamos ubicar tu cuenta más rápido. Si el motivo es una solicitud u orden, agrega el identificador o el título para facilitar la revisión.",
        ),
      ),
      legalSection(
        "Plazos de atención",
        paragraph(
          "Los plazos de respuesta están ",
          pending(PENDING_RESPONSE),
          " y se informarán en esta página cuando sean definidos.",
        ),
      ),
      legalSection(
        "Documentos relacionados",
        bullets([
          h("span", {}, internalLink("Información legal", routes.legal), "."),
          h("span", {}, internalLink("Política de Privacidad", routes.privacy), "."),
          h("span", {}, internalLink("Términos y Condiciones", routes.terms), "."),
          h("span", {}, internalLink("Tratamiento de Datos Personales", routes.dataTreatment), "."),
        ]),
      ),
    ],
  });
}
