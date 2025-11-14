import { useQuery } from "@tanstack/react-query"
import { OrdersService } from "@/client"

export function useOrder(orderId: number) {
  return useQuery({
    queryKey: ["order", orderId],
    queryFn: () => OrdersService.getOrder({ orderId }),
    enabled: orderId > 0,
    staleTime: 30 * 60 * 1000, // 30 minutes
  })
}

export function useOrdersBulk(orderIds: number[]) {
  return useQuery({
    queryKey: ["orders", "bulk", orderIds.sort().join(",")],
    queryFn: () =>
      OrdersService.getOrdersBulk({
        requestBody: { order_ids: orderIds },
      }),
    enabled: orderIds.length > 0,
    staleTime: 30 * 60 * 1000, // 30 minutes
  })
}
