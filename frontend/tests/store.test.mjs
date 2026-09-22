import assert from "node:assert/strict";
import test from "node:test";

import { store } from "../src/state/store.js";

test("reset limpia el estado de usuario y las notificaciones", () => {
  store.setMe({ user: { id: "a" } });
  store.setNotifications([
    { id: "n1", is_read: false },
    { id: "n2", is_read: true },
  ]);
  assert.equal(store.get().unread, 1);

  store.reset();

  assert.equal(store.get().me, null);
  assert.deepEqual(store.get().notifications, []);
  assert.equal(store.get().unread, 0);
});
