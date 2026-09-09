self.addEventListener("push", (event) => {
  let data = { title: "Juve Momentum Index", body: "" };
  if (event.data) {
    try {
      data = event.data.json();
    } catch {
      data = { title: "Juve Momentum Index", body: event.data.text() };
    }
  }

  event.waitUntil(
    self.registration.showNotification(data.title || "Juve Momentum Index", {
      body: data.body || "",
    })
  );
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  event.waitUntil(
    self.clients.matchAll({ type: "window", includeUncontrolled: true }).then((clients) => {
      for (const client of clients) {
        if ("focus" in client) return client.focus();
      }
      if (self.clients.openWindow) return self.clients.openWindow("/");
    })
  );
});
