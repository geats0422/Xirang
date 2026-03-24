import { computed, ref } from "vue";
import { useRoute, useRouter } from "vue-router";

const ROUTE_PULSE_MS = 220;

export const useRouteNavigation = () => {
  const router = useRouter();
  const route = useRoute();
  const routingTarget = ref<string | null>(null);

  const currentPath = computed(() => route.path);

  const isActiveRoute = (targetRoute: string) => currentPath.value === targetRoute;

  const clearRoutingTargetLater = (targetRoute: string) => {
    if (typeof window === "undefined") {
      routingTarget.value = null;
      return;
    }

    window.setTimeout(() => {
      if (routingTarget.value === targetRoute) {
        routingTarget.value = null;
      }
    }, ROUTE_PULSE_MS);
  };

  const navigateTo = async (targetRoute: string) => {
    if (isActiveRoute(targetRoute)) {
      return;
    }

    routingTarget.value = targetRoute;

    try {
      await router.push(targetRoute);
    } finally {
      clearRoutingTargetLater(targetRoute);
    }
  };

  return {
    currentPath,
    isActiveRoute,
    navigateTo,
    route,
    router,
    routingTarget,
  };
};
