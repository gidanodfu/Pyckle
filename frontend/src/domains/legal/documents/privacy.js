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
import { pending, paragraph, bullets, legalSection, LegalShell, PENDING_RETENTION, PENDING_RESPONSE } from "../layout.js";

export function PrivacyPolicyPage() {
  return LegalShell({
    title: "Política de Privacidad",
    subtitle: "Cómo Pyckle recopila, usa y protege la información de las personas usuarias.",
    current: routes.privacy,
    children: [
      legalSection(
        "Responsable del tratamiento",
        paragraph(
          "El responsable del tratamiento de los datos personales es la entidad titular de Pyckle. Sus datos completos figuran como ",
          pending(site.legalEntity),
          " y están pendientes de configuración.",
        ),
        paragraph("Este documento se redacta en el marco de la Ley N.º 29733, Ley de Protección de Datos Personales de Perú, y su reglamento."),
      ),
      legalSection(
        "Datos que recopilamos",
        bullets([
          h("span", {}, h("b", {}, "Identificación: "), "nombre completo y correo electrónico. La contraseña se almacena mediante hash Argon2 y nunca en texto plano."),
          h("span", {}, h("b", {}, "Contacto: "), "teléfono celular normalizado en formato +51."),
          h("span", {}, h("b", {}, "Ubicación: "), "departamento, provincia y distrito de residencia o atención. La dirección exacta es privada y solo se comparte con el técnico asignado cuando la cotización de una reparación a domicilio fue aceptada."),
          h("span", {}, h("b", {}, "Perfil: "), "rol (cliente o técnico), descripción profesional, años de experiencia, especialidades y, si corresponde, dirección del local o taller."),
          h("span", {}, h("b", {}, "Actividad en la plataforma: "), "solicitudes de reparación, descripciones, imágenes adjuntas, cotizaciones, órdenes, estados, reseñas y calificaciones."),
          h("span", {}, h("b", {}, "Comunicaciones: "), "mensajes intercambiados en el chat interno de cada reparación."),
          h("span", {}, h("b", {}, "Datos técnicos de seguridad: "), "dirección IP y marcas de tiempo asociadas al inicio de sesión, tokens de acceso y registros necesarios para prevenir abuso y proteger las cuentas."),
        ]),
      ),
      legalSection(
        "Finalidades del uso",
        bullets([
          "Crear y administrar la cuenta y permitir el inicio de sesión.",
          "Conectar solicitudes de reparación con técnicos según especialidad y zona.",
          "Gestionar cotizaciones, órdenes, estados, reseñas y notificaciones.",
          "Habilitar la comunicación entre cliente y técnico.",
          "Proteger la plataforma, prevenir fraudes y aplicar límites de intentos de acceso.",
          "Cumplir obligaciones legales aplicables y atender solicitudes de las personas titulares.",
        ]),
      ),
      legalSection(
        "Base del tratamiento",
        bullets([
          "Consentimiento de la persona titular al registrarse y aceptar los Términos y Condiciones.",
          "Ejecución de la relación contractual entre la persona usuaria y Pyckle.",
          "Interés legítimo en la seguridad, prevención de abuso y correcto funcionamiento del servicio.",
          "Cumplimiento de obligaciones legales cuando corresponda.",
        ]),
      ),
      legalSection(
        "Conservación",
        paragraph(
          "Los datos se conservan mientras la cuenta esté activa y durante los plazos necesarios para atender obligaciones legales o reclamos. Los plazos específicos están ",
          pending(PENDING_RETENTION),
          ".",
        ),
      ),
      legalSection(
        "Seguridad",
        bullets([
          "Contraseñas protegidas con Argon2 y sesiones con tokens JWT de corta duración y rotación de refresh tokens.",
          "Autorización por rol y por relación con cada recurso (cliente, técnico asignado o administrador).",
          "Límite de intentos de inicio de sesión con bloqueo temporal.",
          "Imágenes servidas mediante un endpoint propio de Pyckle; la base de datos guarda claves de almacenamiento, no URLs públicas de terceros.",
          "Comunicaciones cifradas mediante HTTPS en los entornos de producción.",
        ]),
      ),
      legalSection(
        "Terceros y proveedores",
        bullets([
          h("span", {}, h("b", {}, "Almacenamiento de imágenes: "), "Supabase Storage cuando el proyecto se configura con almacenamiento S3; en desarrollo se usa almacenamiento local."),
          h("span", {}, h("b", {}, "Infraestructura: "), "servidores de despliegue y proxy/CDN según la configuración de producción (por ejemplo, Cloudflare delante del servidor propio)."),
          "No se utilizan los datos para publicidad ni se venden a terceros.",
        ]),
      ),
      legalSection(
        "Derechos de la persona titular",
        paragraph(
          "Puedes solicitar acceso, rectificación, cancelación u oposición al tratamiento de tus datos personales (derechos ARCO), así como revocar tu consentimiento cuando corresponda. Para ejercerlos, escríbenos a ",
          pending(site.privacyEmail),
          ". La solicitud debe permitir verificar tu identidad y describir el derecho que deseas ejercer.",
        ),
        paragraph(`Plazo de atención: ${PENDING_RESPONSE}.`),
      ),
      legalSection(
        "Menores de edad",
        paragraph("La plataforma está dirigida a personas mayores de edad. No se recopilan deliberadamente datos de menores de edad."),
      ),
      legalSection(
        "Cambios a esta política",
        paragraph("Pyckle puede actualizar esta política para reflejar cambios en el servicio o en la normativa. La versión vigente se publicará en esta misma página."),
      ),
    ],
  });
}
