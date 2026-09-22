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

from app.db.base import Base
from app.models.chat import Conversation, Message
from app.models.customer import CustomerProfile
from app.models.enums import (
    ConversationStatus,
    CostKind,
    Modality,
    NotificationType,
    OrderEventType,
    PermissionCode,
    PriceChangeStatus,
    QuotationStatus,
    RepairResult,
    RepairStatus,
    RequestStatus,
    RoleName,
)
from app.models.geo import Department, District, Province
from app.models.notification import Notification
from app.models.oauth import OAuthAccount
from app.models.order import (
    Order,
    OrderCostItem,
    OrderEvent,
    OrderPriceChange,
    RepairReport,
)
from app.models.quotation import Quotation, QuotationItem
from app.models.repair import RepairRequest, RepairRequestImage
from app.models.review import Review
from app.models.technician import Specialty, Technician, technician_specialties
from app.models.user import Permission, Role, User, role_permissions, user_roles

__all__ = [
    "Base",
    "Conversation",
    "ConversationStatus",
    "CostKind",
    "CustomerProfile",
    "Department",
    "District",
    "Message",
    "Modality",
    "Notification",
    "NotificationType",
    "OAuthAccount",
    "Order",
    "OrderCostItem",
    "OrderEvent",
    "OrderEventType",
    "OrderPriceChange",
    "Permission",
    "PermissionCode",
    "PriceChangeStatus",
    "Province",
    "Quotation",
    "QuotationItem",
    "QuotationStatus",
    "RepairReport",
    "RepairRequest",
    "RepairRequestImage",
    "RepairResult",
    "RepairStatus",
    "RequestStatus",
    "Review",
    "Role",
    "RoleName",
    "Specialty",
    "Technician",
    "User",
    "role_permissions",
    "technician_specialties",
    "user_roles",
]
