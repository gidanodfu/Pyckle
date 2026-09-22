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

import { routes, site } from "../../../lib/paths.js";
import { pending, internalLink, paragraph, bullets, legalSection, LegalShell } from "../layout.js";

export function TermsPage() {
  return LegalShell({
    title: "Términos y Condiciones",
    subtitle: "Reglas de uso de la plataforma Pyckle.",
    current: routes.terms,
    children: [
      legalSection(
        "1. Qué es Pyckle",
        paragraph(
          "Pyckle es una plataforma tecnológica que conecta clientes con técnicos independientes para la reparación de dispositivos en Perú. Pyckle no repara dispositivos por sí misma.",
        ),
      ),
      legalSection(
        "2. Alcance de la plataforma",
        paragraph(
          "La plataforma permite publicar solicitudes, recibir cotizaciones, aceptar una oferta, generar una orden de reparación, comunicarse por chat y calificar el servicio. Pyckle no es parte del contrato de reparación entre cliente y técnico.",
        ),
      ),
      legalSection(
        "3. Cuentas de usuario",
        bullets([
          "Debes proporcionar datos veraces y mantenerlos actualizados.",
          "Eres responsable de la confidencialidad de tu contraseña y de la actividad de tu cuenta.",
          "El teléfono se valida y normaliza; una cuenta no puede reutilizar el teléfono de otra persona.",
          "Debes ser mayor de edad para registrarte.",
        ]),
      ),
      legalSection(
        "4. Rol del cliente",
        bullets([
          "Describe el problema con la mayor precisión posible y adjunta imágenes cuando aporten valor.",
          "Proporciona una ubicación válida; en solicitudes a domicilio se exige una dirección de servicio.",
          "La dirección exacta es privada y solo se comparte con el técnico asignado tras aceptar su cotización.",
          "Acepta que las cotizaciones son ofertas de técnicos independientes y que el precio final puede variar si el diagnóstico cambia, previo acuerdo entre las partes.",
        ]),
      ),
      legalSection(
        "5. Rol del técnico",
        bullets([
          "Actúa como profesional independiente; no existe relación laboral con Pyckle.",
          "Debe declarar sus especialidades y zona de atención de forma correcta.",
          "Si ofrece atención en taller, debe registrar la dirección del local.",
          "Es responsable de la calidad, seguridad y legalidad de los trabajos que realiza, así como de la información que publica en su perfil.",
        ]),
      ),
      legalSection(
        "6. Solicitudes de reparación",
        paragraph(
          "Las solicitudes quedan visibles para técnicos compatibles con la especialidad y la zona. El cliente puede editarlas o cancelarlas mientras estén abiertas o cotizadas. El contenido publicado no debe ser ilegal, ofensivo ni contener datos de terceros sin autorización.",
        ),
      ),
      legalSection(
        "7. Cotizaciones",
        bullets([
          "Cada técnico puede enviar una cotización por solicitud, con precio, diagnóstico preliminar y tiempo estimado.",
          "El cliente puede aceptar una sola cotización; al hacerlo se crea la orden y las demás cotizaciones pendientes se rechazan.",
          "El técnico puede retirar su cotización mientras siga pendiente.",
          "Las cotizaciones son estimaciones: el precio final se acuerda entre cliente y técnico.",
        ]),
      ),
      legalSection(
        "8. Comunicación entre usuarios",
        paragraph(
          "El chat es el canal previsto para coordinar la reparación. No compartas contraseñas, datos bancarios ni información sensible por este medio. El uso del chat para acoso, spam o actividades ilícitas puede provocar la suspensión de la cuenta.",
        ),
      ),
      legalSection(
        "9. Órdenes de reparación",
        paragraph(
          "La orden registra el estado de la reparación (pendiente, en progreso, completada o cancelada) y su historial. Cuando la orden finaliza o se cancela, el chat se archiva: deja de admitir mensajes y conserva el historial disponible para consulta.",
        ),
      ),
      legalSection(
        "10. Pagos",
        paragraph(
          "Pyckle no procesa pagos en línea ni cobra comisiones dentro de la plataforma en esta versión. El pago del servicio se acuerda y realiza directamente entre cliente y técnico por los medios que ambos elijan. La emisión de comprobantes de pago, cuando corresponda, es responsabilidad del técnico.",
        ),
      ),
      legalSection(
        "11. Contenido generado por usuarios",
        paragraph(
          "Conservas la titularidad de tus contenidos (textos, imágenes y reseñas), pero otorgas a Pyckle una autorización limitada para almacenarlos, mostrarlos y procesarlos con la única finalidad de operar la plataforma. No publiques contenido que infrinja derechos de terceros.",
        ),
      ),
      legalSection(
        "12. Propiedad intelectual",
        paragraph(
          "El nombre, el logo, el software y los elementos gráficos de Pyckle pertenecen a sus titulares. No está permitido copiarlos, modificarlos ni usarlos sin autorización.",
        ),
      ),
      legalSection(
        "13. Reseñas",
        paragraph(
          "Las reseñas solo pueden crearse sobre órdenes completadas y reflejan la opinión de quien las escribe. Las calificaciones promedio y la cantidad de reseñas se muestran en los perfiles públicos de los técnicos.",
        ),
      ),
      legalSection(
        "14. Limitación de responsabilidad",
        paragraph(
          "Pyckle pone a disposición la plataforma tal como está y no garantiza la disponibilidad ininterrumpida del servicio ni el resultado de los trabajos de reparación, que son responsabilidad de cada técnico. En la medida permitida por la ley peruana, Pyckle no responde por daños indirectos derivados del uso de la plataforma o de los servicios contratados entre usuarios.",
        ),
      ),
      legalSection(
        "15. Suspensión y cancelación de cuentas",
        paragraph(
          "Pyckle puede suspender o cancelar cuentas que incumplan estos términos, intenten manipular la plataforma, publiquen contenido prohibido o afecten a otras personas usuarias. La persona usuaria puede solicitar la eliminación de su cuenta mediante el canal de contacto.",
        ),
      ),
      legalSection(
        "16. Modificaciones de los términos",
        paragraph("Estos términos pueden actualizarse. La versión vigente se publica en esta página y su uso continuado implica la aceptación de los cambios."),
      ),
      legalSection(
        "17. Legislación y jurisdicción",
        paragraph("Estos términos se rigen por la legislación de la República del Perú. Cualquier controversia se someterá a los tribunales competentes conforme a la normativa aplicable."),
      ),
      legalSection(
        "18. Contacto",
        paragraph("Para consultas sobre estos términos escríbenos a ", pending(site.legalEmail), " o visita ", internalLink("Contacto", routes.contact), "."),
      ),
    ],
  });
}
