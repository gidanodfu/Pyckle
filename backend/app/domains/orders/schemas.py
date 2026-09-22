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

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import Field

from app.domains.quotations.schemas import QuotationRead
from app.domains.repair_requests.schemas import TechnicianBrief
from app.domains.users.schemas import UserBrief
from app.models.enums import (
    CostKind,
    Modality,
    OrderEventType,
    PriceChangeStatus,
    RepairResult,
    RepairStatus,
)
from app.schemas.common import MAX_MONEY, NonBlankStr, ORMModel


class OrderEventRead(ORMModel):
    id: uuid.UUID
    event_type: OrderEventType
    old_status: RepairStatus | None = None
    new_status: RepairStatus | None = None
    description: str | None = None
    visible_to_customer: bool
    actor: UserBrief | None = None
    created_at: datetime


class PriceChangeRead(ORMModel):
    id: uuid.UUID
    previous_price: Decimal
    new_price: Decimal
    reason: str
    status: PriceChangeStatus
    decided_note: str | None = None
    decided_at: datetime | None = None
    created_at: datetime


class PriceChangeCreate(ORMModel):
    new_price: Decimal = Field(ge=0, le=MAX_MONEY)
    reason: NonBlankStr = Field(min_length=5, max_length=2000)


class PriceChangeDecision(ORMModel):
    note: str | None = Field(default=None, max_length=1000)


class CostItemRead(ORMModel):
    id: uuid.UUID
    kind: CostKind
    description: str
    amount: Decimal
    visible_to_customer: bool
    created_at: datetime


class CostItemCreate(ORMModel):
    kind: CostKind = CostKind.OTHER
    description: NonBlankStr = Field(min_length=2, max_length=255)
    amount: Decimal = Field(ge=0, le=MAX_MONEY)
    visible_to_customer: bool = False


class ReportRead(ORMModel):
    id: uuid.UUID
    version: int
    content_type: str
    size_bytes: int
    generated_at: datetime
    download_url: str | None = None


class OrderRequestBrief(ORMModel):
    id: uuid.UUID
    title: str
    status: str
    modality: Modality
    specialty_name: str | None = None
    district_name: str | None = None
    province_name: str | None = None
    department_name: str | None = None


class OrderListItem(ORMModel):
    id: uuid.UUID
    request_id: uuid.UUID
    quotation_id: uuid.UUID
    status: RepairStatus
    result: RepairResult | None = None
    final_price: Decimal
    customer: UserBrief
    technician: TechnicianBrief
    request: OrderRequestBrief
    has_pending_price_change: bool = False
    has_report: bool = False
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None


class OrderRead(ORMModel):
    id: uuid.UUID
    request_id: uuid.UUID
    quotation_id: uuid.UUID
    status: RepairStatus
    result: RepairResult | None = None
    final_price: Decimal
    received_at: datetime | None = None
    completed_at: datetime | None = None
    customer: UserBrief
    technician: TechnicianBrief
    quotation: QuotationRead
    request: OrderRequestBrief
    # Dirección de servicio: solo para el cliente, el técnico asignado o un admin.
    service_address: str | None = None
    diagnosis: str | None = None
    work_performed: str | None = None
    tests_performed: str | None = None
    not_repairable_reason: str | None = None
    # Solo para el técnico asignado o un administrador.
    technician_notes: str | None = None
    events: list[OrderEventRead] = []
    price_changes: list[PriceChangeRead] = []
    cost_items: list[CostItemRead] = []
    report: ReportRead | None = None
    report_versions: int = 0
    has_pending_price_change: bool = False
    has_review: bool = False
    created_at: datetime
    updated_at: datetime


class OrderStatusUpdate(ORMModel):
    status: RepairStatus
    note: str | None = Field(default=None, max_length=1000)


class RepairDetailsUpdate(ORMModel):
    diagnosis: NonBlankStr | None = Field(default=None, max_length=5000)
    work_performed: NonBlankStr | None = Field(default=None, max_length=5000)
    tests_performed: NonBlankStr | None = Field(default=None, max_length=5000)
    technician_notes: NonBlankStr | None = Field(default=None, max_length=5000)


class OrderComplete(ORMModel):
    """Cierre con resultado REPAIRED. Requiere los datos de cierre y el informe."""

    final_price: Decimal | None = Field(default=None, ge=0, le=MAX_MONEY)
    diagnosis: NonBlankStr | None = Field(default=None, max_length=5000)
    work_performed: NonBlankStr | None = Field(default=None, max_length=5000)
    tests_performed: NonBlankStr | None = Field(default=None, max_length=5000)
    note: str | None = Field(default=None, max_length=1000)


class OrderNotRepairable(ORMModel):
    reason: NonBlankStr = Field(min_length=10, max_length=5000)
    diagnosis: NonBlankStr = Field(min_length=10, max_length=5000)
    recommendation: NonBlankStr | None = Field(default=None, max_length=5000)
    note: str | None = Field(default=None, max_length=1000)


class OrderCancel(ORMModel):
    reason: NonBlankStr = Field(min_length=5, max_length=2000)
