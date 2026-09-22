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

import {
  AlertCircle,
  AlertTriangle,
  Archive,
  ArrowLeft,
  ArrowRight,
  BadgeCheck,
  Ban,
  Bell,
  BellRing,
  Calendar,
  Check,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  CircleCheck,
  CircleDollarSign,
  CircleX,
  ClipboardCheck,
  ClipboardList,
  Clock,
  CreditCard,
  Database,
  ExternalLink,
  Eye,
  EyeOff,
  FileDown,
  FileText,
  Filter,
  Gamepad2,
  Hammer,
  Home,
  ImageOff,
  Inbox,
  Info,
  Laptop,
  LayoutDashboard,
  LifeBuoy,
  Loader2,
  Lock,
  LogIn,
  LogOut,
  Mail,
  MapPin,
  Menu,
  MessageSquare,
  Monitor,
  Package,
  Pencil,
  Phone,
  Plus,
  Printer,
  Receipt,
  ReceiptText,
  Save,
  ScanSearch,
  Search,
  Send,
  Settings,
  ShieldCheck,
  Smartphone,
  Star,
  Store,
  Tablet,
  Trash2,
  TrendingUp,
  Tv,
  User,
  UserCog,
  Users,
  Wrench,
  X,
  Moon,
  Sun,
} from "lucide";

const SVG_NS = "http://www.w3.org/2000/svg";

const ICONS = {
  AlertCircle,
  AlertTriangle,
  Archive,
  ArrowLeft,
  ArrowRight,
  BadgeCheck,
  Ban,
  Bell,
  BellRing,
  Calendar,
  Check,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  CircleCheck,
  CircleDollarSign,
  CircleX,
  ClipboardCheck,
  ClipboardList,
  Clock,
  CreditCard,
  Database,
  ExternalLink,
  Eye,
  EyeOff,
  FileDown,
  FileText,
  Filter,
  Gamepad2,
  Hammer,
  Home,
  ImageOff,
  Inbox,
  Info,
  Laptop,
  LayoutDashboard,
  LifeBuoy,
  Loader2,
  Lock,
  LogIn,
  LogOut,
  Mail,
  MapPin,
  Menu,
  MessageSquare,
  Monitor,
  Package,
  Pencil,
  Phone,
  Plus,
  Printer,
  Receipt,
  ReceiptText,
  Save,
  ScanSearch,
  Search,
  Send,
  Settings,
  ShieldCheck,
  Smartphone,
  Star,
  Store,
  Tablet,
  Trash2,
  TrendingUp,
  Tv,
  User,
  UserCog,
  Users,
  Wrench,
  X,
  Moon,
  Sun,
};

function toKebabCase(name) {
  return name
    .replace(/([a-z0-9])([A-Z])/g, "$1-$2")
    .replace(/([A-Za-z])(\d)/g, "$1-$2")
    .toLowerCase();
}

const ICON_NODES = Object.fromEntries(
  Object.entries(ICONS).map(([name, node]) => [toKebabCase(name), node]),
);

function appendChildren(parent, children = []) {
  for (const [tag, attrs, nested] of children) {
    const child = document.createElementNS(SVG_NS, tag);
    for (const [attr, value] of Object.entries(attrs || {})) child.setAttribute(attr, value);
    if (nested && nested.length) appendChildren(child, nested);
    parent.append(child);
  }
}

/**
 * Construye el SVG del icono de forma síncrona (sin observer ni placeholders).
 * Los datos provienen de lucide, por lo que no hay reescaneo del DOM.
 */
export function icon(name, { size = 18, class: extra = "", stroke = 2 } = {}) {
  const node = ICON_NODES[name];
  const svg = document.createElementNS(SVG_NS, "svg");
  for (const [attr, value] of Object.entries((node && node[1]) || {})) {
    svg.setAttribute(attr, value);
  }
  svg.setAttribute("width", String(size));
  svg.setAttribute("height", String(size));
  svg.setAttribute("stroke-width", String(stroke));
  svg.setAttribute("class", `lucide lucide-${name} inline-flex shrink-0 ${extra}`.trim());
  if (!node) svg.setAttribute("data-icon-missing", name);
  appendChildren(svg, (node && node[2]) || []);
  return svg;
}
