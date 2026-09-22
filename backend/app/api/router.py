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

from fastapi import APIRouter

from app.api import ws
from app.domains.admin import router as admin_router
from app.domains.auth import router as auth_router
from app.domains.conversations import router as conversations_router
from app.domains.geo import router as geo_router
from app.domains.media import router as media_router
from app.domains.notifications import router as notifications_router
from app.domains.orders import router as orders_router
from app.domains.quotations import router as quotations_router
from app.domains.repair_requests import router as repair_requests_router
from app.domains.reviews import router as reviews_router
from app.domains.technicians import router as technicians_router
from app.domains.technicians import specialties_router
from app.domains.users import router as users_router

api_router = APIRouter()
api_router.include_router(ws.ticket_router)
api_router.include_router(auth_router.router)
api_router.include_router(users_router.router)
api_router.include_router(geo_router.router)
api_router.include_router(media_router.router)
api_router.include_router(specialties_router.router)
api_router.include_router(technicians_router.router)
api_router.include_router(repair_requests_router.router)
api_router.include_router(quotations_router.router)
api_router.include_router(orders_router.router)
api_router.include_router(conversations_router.router)
api_router.include_router(reviews_router.router)
api_router.include_router(notifications_router.router)
api_router.include_router(admin_router.router)
