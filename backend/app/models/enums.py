# Copyright (C) 2026 Josue David (gidanodfu)
# https://github.com/gidanodfu
#
# This file is part of Pyckle.
#
# Pyckle is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of
# the License, or (at your option) any later version.
#
# Pyckle is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with Pyckle. If not, see <https://www.gnu.org/licenses/>.

from enum import StrEnum


class RoleName(StrEnum):
    CUSTOMER = "customer"
    TECHNICIAN = "technician"
    ADMIN = "admin"


class PermissionCode(StrEnum):
    # Solicitudes de reparación
    REPAIR_REQUEST_CREATE = "repair_request:create"
    REPAIR_REQUEST_READ_OWN = "repair_request:read_own"
    REPAIR_REQUEST_READ_AVAILABLE = "repair_request:read_available"
    REPAIR_REQUEST_MODERATE = "repair_request:moderate"
    # Cotizaciones
    QUOTATION_CREATE = "quotation:create"
    QUOTATION_READ = "quotation:read"
    # Ordenes / reparaciones
    ORDER_MANAGE_ASSIGNED = "order:manage_assigned"
    ORDER_READ_OWN = "order:read_own"
    ORDER_READ_ALL = "order:read_all"
    # Chat
    CHAT_PARTICIPATE = "chat:participate"
    # Reseñas
    REVIEW_CREATE = "review:create"
    # Administracion
    ADMIN_USERS = "admin:users"
    ADMIN_SPECIALTIES = "admin:specialties"
    ADMIN_TECHNICIANS_VERIFY = "admin:technicians_verify"
    ADMIN_ORDERS = "admin:orders"
    ADMIN_REPORTS = "admin:reports"
    ADMIN_ROLES = "admin:roles"


class RequestStatus(StrEnum):
    OPEN = "open"
    QUOTED = "quoted"
    ACCEPTED = "accepted"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Modality(StrEnum):
    HOME = "home"
    WORKSHOP = "workshop"


class QuotationStatus(StrEnum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class RepairStatus(StrEnum):
    """Estado técnico de la reparación (sobre ``orders``).

    Aceptar una cotización no implica haber recibido el equipo: la orden nace en
    ``AWAITING_RECEIPT``. Los estados terminales (``COMPLETED``/``CANCELLED``) se
    alcanzan mediante acciones específicas, no con un PATCH genérico.
    """

    AWAITING_RECEIPT = "awaiting_receipt"
    RECEIVED = "received"
    DIAGNOSIS = "diagnosis"
    WAITING_CUSTOMER = "waiting_customer"
    WAITING_PART = "waiting_part"
    IN_REPAIR = "in_repair"
    TESTING = "testing"
    READY = "ready"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


# Transiciones permitidas vía PATCH /orders/{id}/status (solo no terminales).
ALLOWED_STATUS_TRANSITIONS: dict[RepairStatus, set[RepairStatus]] = {
    RepairStatus.AWAITING_RECEIPT: {RepairStatus.RECEIVED},
    RepairStatus.RECEIVED: {RepairStatus.DIAGNOSIS},
    RepairStatus.DIAGNOSIS: {
        RepairStatus.WAITING_CUSTOMER,
        RepairStatus.WAITING_PART,
        RepairStatus.IN_REPAIR,
    },
    RepairStatus.WAITING_CUSTOMER: {RepairStatus.DIAGNOSIS, RepairStatus.IN_REPAIR},
    RepairStatus.WAITING_PART: {RepairStatus.IN_REPAIR, RepairStatus.WAITING_CUSTOMER},
    RepairStatus.IN_REPAIR: {RepairStatus.TESTING, RepairStatus.WAITING_PART},
    RepairStatus.TESTING: {RepairStatus.READY, RepairStatus.IN_REPAIR},
    RepairStatus.READY: {RepairStatus.TESTING},
    RepairStatus.COMPLETED: set(),
    RepairStatus.CANCELLED: set(),
}

TERMINAL_REPAIR_STATUSES = {RepairStatus.COMPLETED, RepairStatus.CANCELLED}

# Estados desde los que un cliente puede cancelar (antes del trabajo facturable).
CUSTOMER_CANCELLABLE_STATUSES = {
    RepairStatus.AWAITING_RECEIPT,
    RepairStatus.RECEIVED,
    RepairStatus.DIAGNOSIS,
    RepairStatus.WAITING_CUSTOMER,
    RepairStatus.WAITING_PART,
}


class RepairResult(StrEnum):
    REPAIRED = "repaired"
    NOT_REPAIRABLE = "not_repairable"
    CANCELLED = "cancelled"


class OrderEventType(StrEnum):
    STATUS_CHANGED = "status_changed"
    RECEIVED = "received"
    DIAGNOSIS_STARTED = "diagnosis_started"
    DIAGNOSIS_COMPLETED = "diagnosis_completed"
    PART_REQUESTED = "part_requested"
    REPAIR_STARTED = "repair_started"
    TESTING_STARTED = "testing_started"
    PRICE_CHANGE_PROPOSED = "price_change_proposed"
    PRICE_CHANGE_APPROVED = "price_change_approved"
    PRICE_CHANGE_REJECTED = "price_change_rejected"
    COMPLETED = "completed"
    NOT_REPAIRABLE = "not_repairable"
    CANCELLED = "cancelled"
    REPORT_GENERATED = "report_generated"
    NOTE = "note"


class PriceChangeStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class CostKind(StrEnum):
    PART = "part"
    LABOR = "labor"
    OTHER = "other"


class ConversationStatus(StrEnum):
    OPEN = "open"
    CLOSED = "closed"
    ARCHIVED = "archived"


class NotificationType(StrEnum):
    QUOTATION_CREATED = "quotation_created"
    QUOTATION_ACCEPTED = "quotation_accepted"
    ORDER_STATUS_CHANGED = "order_status_changed"
    MESSAGE_NEW = "message_new"
    REVIEW_CREATED = "review_created"
    REPAIR_RECEIVED = "repair_received"
    REPAIR_DIAGNOSIS_COMPLETED = "repair_diagnosis_completed"
    PRICE_CHANGE_REQUESTED = "price_change_requested"
    PRICE_CHANGE_APPROVED = "price_change_approved"
    PRICE_CHANGE_REJECTED = "price_change_rejected"
    REPAIR_IN_PROGRESS = "repair_in_progress"
    REPAIR_READY = "repair_ready"
    REPAIR_COMPLETED = "repair_completed"
    REPAIR_NOT_REPAIRABLE = "repair_not_repairable"
    REPAIR_CANCELLED = "repair_cancelled"
    REPORT_AVAILABLE = "report_available"
    SYSTEM = "system"
