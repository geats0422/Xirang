import { ref } from "vue";
import { getShopInventory, type ShopInventoryItem } from "../api/shop";

export function useInventory() {
  const inventory = ref<ShopInventoryItem[]>([]);
  const isLoading = ref(false);

  async function refresh() {
    isLoading.value = true;
    try {
      inventory.value = await getShopInventory();
    } finally {
      isLoading.value = false;
    }
  }

  function quantityOf(itemCode: string): number {
    return inventory.value.find((i) => i.item_code === itemCode)?.quantity ?? 0;
  }

  return { inventory, isLoading, refresh, quantityOf };
}
