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
import { table } from "../../../components/ui/index.js";
import { routes, site } from "../../../lib/paths.js";
import { pending, internalLink, paragraph, bullets, legalSection, LegalShell, PENDING_RETENTION, PENDING_RESPONSE } from "../layout.js";

export function DataTreatmentPage() {
  return LegalShell({
    title: "Tratamiento de Datos Personales",
    subtitle: "Detalle operativo del tratamiento de datos en Pyckle.",
    current: routes.dataTreatment,
    children: [
      legalSection(
        "En qué se diferencia de la Política de Privacidad",
        paragraph(
          "La Política de Privacidad describe el marco general del uso de datos. Esta página detalla, por categoría, qué datos se tratan, con qué finalidad, sobre qué base y por cuánto tiempo, en la operación diaria de la plataforma.",
        ),
      ),
      legalSection(
        "Categorías, finalidades y base del tratamiento",
        table(
          [
            "Categoría",
            "Datos",
            { label: "Finalidad", align: "center" },
            "Base",
          ],
          [
            ["Identificación", "Nombre y correo", { label: "Cuenta y acceso", align: "center" }, "Consentimiento / contrato"],
            ["Contacto", "Teléfono +51", { label: "Coordinación", align: "center" }, "Consentimiento"],
            ["Ubicación", "Departamento, provincia y distrito", { label: "Filtros por zona", align: "center" }, "Consentimiento"],
            ["Perfil", "Rol, bio, especialidades, local", { label: "Perfil público", align: "center" }, "Consentimiento"],
            ["Servicio", "Solicitudes, imágenes, cotizaciones, órdenes", { label: "Prestar el servicio", align: "center" }, "Contrato"],
            ["Comunicaciones", "Mensajes del chat y notificaciones", { label: "Coordinación", align: "center" }, "Contrato"],
            ["Seguridad", "IP, fecha de acceso, tokens", { label: "Prevenir abuso", align: "center" }, "Interés legítimo"],
          ],
        ),
        paragraph("La dirección exacta del cliente se trata con acceso restringido: solo el cliente, un administrador o el técnico asignado tras aceptar la cotización pueden consultarla."),
      ),
      legalSection(
        "Tratamiento necesario para prestar el servicio",
        paragraph(
          "Para publicar una solicitud, recibir cotizaciones, generar una orden, mantener el chat, calcular reseñas y gestionar perfiles, Pyckle trata los datos de servicio y comunicación indicados en la tabla. Sin estos datos no es posible prestar la funcionalidad principal.",
        ),
      ),
      legalSection(
        "Tratamiento asociado a seguridad",
        bullets([
          "Registro de intentos de inicio de sesión mediante un identificador derivado (hash de correo e IP) y bloqueo temporal; no se almacena la contraseña.",
          "Tokens JWT de acceso y refresh con rotación y expiración; los refresh se guardan temporalmente en Redis.",
          "Registros técnicos del servidor para diagnosticar errores y detectar abuso.",
        ]),
      ),
      legalSection(
        "Tratamiento asociado a comunicaciones",
        paragraph(
          "Las notificaciones internas y los mensajes del chat se almacenan para mostrar el historial de cada conversación. Pyckle no envía campañas de marketing ni comunica datos a terceros con fines publicitarios.",
        ),
      ),
      legalSection(
        "Almacenamiento",
        bullets([
          "Base de datos PostgreSQL para cuentas, solicitudes, cotizaciones, órdenes, mensajes y reseñas.",
          "Redis para sesiones temporales y límites de seguridad.",
          "Archivos locales del servidor o Supabase Storage para las imágenes de solicitudes, según la configuración del despliegue.",
        ]),
      ),
      legalSection(
        "Conservación y supresión",
        paragraph(
          "Los datos se conservan mientras la cuenta esté activa y el tiempo necesario para atender reclamos o cumplir obligaciones legales. Los plazos concretos están ",
          pending(PENDING_RETENTION),
          ". La eliminación de la cuenta elimina o anonimiza los datos personales, salvo aquello que deba conservarse por mandato legal.",
        ),
      ),
      legalSection(
        "Derechos del titular y procedimiento",
        bullets([
          "Puedes solicitar acceso, rectificación, cancelación u oposición (derechos ARCO), así como revocar el consentimiento otorgado.",
          h(
            "span",
            {},
            "Envía tu solicitud a ",
            pending(site.privacyEmail),
            " indicando nombre completo, correo registrado y el derecho que deseas ejercer.",
          ),
          "Pyckle puede solicitar información adicional para verificar la identidad del solicitante.",
          `Plazo de respuesta: ${PENDING_RESPONSE}.`,
          "Si consideras que tu solicitud no fue atendida, puedes acudir a la Autoridad Nacional de Protección de Datos Personales (ANPDP) del Perú.",
        ]),
      ),
      legalSection(
        "Encargados y transferencias",
        paragraph(
          "Cuando se usa Supabase Storage, las imágenes se alojan en ese proveedor bajo las condiciones del servicio contratado. No se realizan transferencias internacionales distintas a las necesarias para operar la plataforma.",
        ),
      ),
      legalSection(
        "Contacto",
        paragraph("Canal para consultas de privacidad y datos personales: ", pending(site.privacyEmail), ". También puedes usar la página de ", internalLink("Contacto", routes.contact), "."),
      ),
    ],
  });
}
