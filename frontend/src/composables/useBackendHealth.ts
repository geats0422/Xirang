import { onMounted, ref } from "vue";

import { getBackendHealth, type HealthResponse } from "../api/system";

type BackendStatus = "checking" | "online" | "offline";

export function useBackendHealth() {
  const status = ref<BackendStatus>("checking");
  const serviceName = ref<string>("backend");
  const message = ref<string>("Checking backend connection...");

  onMounted(async () => {
    if (import.meta.env.VITE_ENABLE_BACKEND_HEALTH_CHECK !== "true") {
      status.value = "online";
      message.value = "Backend health check disabled";
      return;
    }

    const controller = new AbortController();
    try {
      const response: HealthResponse = await getBackendHealth(controller.signal);
      serviceName.value = response.service;
      status.value = response.status === "ok" ? "online" : "offline";
      message.value =
        response.status === "ok"
          ? `Connected to ${response.service}`
          : `Backend responded with status: ${response.status}`;
    } catch {
      status.value = "offline";
      message.value = "Cannot reach backend service";
    }
  });

  return {
    status,
    serviceName,
    message,
  };
}
