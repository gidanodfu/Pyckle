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

import { api } from "../../api/client.js";
import { endpoints } from "../../api/endpoints.js";
import { formatDate, h } from "../../components/dom.js";
import { Container } from "../../components/layout/index.js";
import {
  alert,
  badge,
  button,
  card,
  emptyState,
  field,
  input,
  modal,
  pageHeader,
  select,
  table,
  withBusy,
} from "../../components/ui/index.js";
import { createLatestGuard } from "../../lib/latest.js";
import { store } from "../../state/store.js";

export async function UsersPage() {
  const [roles, initial] = await Promise.all([
    api.get(endpoints.admin.roles),
    api.get(endpoints.admin.users({ limit: 50 })),
  ]);
  const me = store.get().me;

  const searchInput = input({ name: "search", placeholder: "Buscar por nombre o correo" });
  const roleSelect = select("role", [
    { value: "", label: "Todos los roles" },
    ...roles.map((role) => ({ value: role.name, label: role.name })),
  ]);
  const tableBox = h("div", { class: "mt-6" });

  function render(users) {
    if (!users.length) {
      tableBox.replaceChildren(emptyState("Sin usuarios", "No se encontraron usuarios."));
      return;
    }
    tableBox.replaceChildren(
      table(
        [
          "Nombre",
          "Correo",
          "Roles",
          { label: "Estado", align: "center" },
          "Registro",
          { label: "Acciones", align: "center" },
        ],
        users.map((user) => [
          user.full_name,
          user.email,
          h(
            "div",
            { class: "flex flex-wrap gap-1" },
            user.roles.map((role) => h("span", { class: "rounded-full bg-slate-100 px-2 py-0.5 text-xs" }, role.name)),
          ),
          user.is_active ? badge("completed", "Activo") : badge("cancelled", "Inactivo"),
          formatDate(user.created_at),
          h(
            "div",
            { class: "flex justify-center gap-2" },
            button("Editar", { variant: "outline", iconName: "pencil", onClick: () => openEdit(user) }),
            user.id !== me.user.id
              ? button("Eliminar", { variant: "danger", iconName: "trash-2", onClick: () => removeUser(user) })
              : null,
          ),
        ]),
      ),
    );
  }
  render(initial.items);

  const guard = createLatestGuard();
  const filterButton = button("Filtrar", { iconName: "filter", onClick: () => reload() });

  async function reload() {
    const isCurrent = guard.next();
    await withBusy(filterButton, async () => {
      let data;
      try {
        data = await api.get(
          endpoints.admin.users({ limit: 50, search: searchInput.value, role: roleSelect.value }),
        );
      } catch (error) {
        if (isCurrent()) window.alert(error.message || "No se pudieron cargar los usuarios");
        return;
      }
      if (!isCurrent()) return;
      render(data.items);
    });
  }

  function openEdit(user) {
    const roleBoxes = h(
      "div",
      { class: "grid gap-2 sm:grid-cols-2" },
      roles.map((role) =>
        h(
          "label",
          { class: "flex items-center gap-2 text-sm" },
          h("input", { type: "checkbox", name: "roles", value: role.name, checked: user.roles.some((item) => item.name === role.name) }),
          role.name,
        ),
      ),
    );
    const active = h("input", { type: "checkbox", name: "is_active", checked: user.is_active });
    const verified = h("input", { type: "checkbox", name: "is_verified", checked: user.is_verified });
    const errorBox = h("div", {});
    const saveButton = button("Guardar", { type: "submit", class: "w-full", iconName: "save" });
    const form = h(
      "form",
      { class: "space-y-4" },
      errorBox,
      h("div", { class: "text-sm text-slate-500" }, user.email),
      field("Roles", roleBoxes),
      h(
        "div",
        { class: "flex gap-4" },
        h("label", { class: "flex items-center gap-2 text-sm" }, active, "Cuenta activa"),
        h("label", { class: "flex items-center gap-2 text-sm" }, verified, "Verificado"),
      ),
      saveButton,
    );
    const dialog = modal("Editar usuario", form);
    document.body.append(dialog);
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const data = new FormData(form);
      await withBusy(saveButton, async () => {
        try {
          await api.patch(endpoints.admin.user(user.id), {
            roles: data.getAll("roles"),
            is_active: data.has("is_active"),
            is_verified: data.has("is_verified"),
          });
          dialog.close();
          reload();
        } catch (error) {
          errorBox.replaceChildren(alert(error.message || "No se pudo actualizar"));
        }
      });
    });
  }

  async function removeUser(user) {
    if (!window.confirm(`¿Eliminar a ${user.full_name}? Esta acción no se puede deshacer.`)) return;
    try {
      await api.del(endpoints.admin.user(user.id));
      await reload();
    } catch (error) {
      window.alert(error.message || "No se pudo eliminar el usuario");
    }
  }

  return Container(
    pageHeader("Gestión de usuarios", "Administra roles, estado y cuentas del marketplace."),
    h(
      "div",
      { class: "mt-6" },
      card(
        h(
          "div",
          { class: "grid gap-4 sm:grid-cols-[1fr_220px_auto]" },
          field("Buscar", searchInput),
          field("Rol", roleSelect),
          h("div", { class: "flex items-end" }, filterButton),
        ),
      ),
    ),
    tableBox,
  );
}
