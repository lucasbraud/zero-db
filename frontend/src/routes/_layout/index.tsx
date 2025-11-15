import { useEffect, useState } from "react"
import {
  Container,
  Heading,
  Stack,
  Text,
} from "@chakra-ui/react"
import { createFileRoute } from "@tanstack/react-router"

import useAuth from "@/hooks/useAuth"
import { useOrdersBulk } from "@/hooks/useOrders"
import { OrderSelector, DeviceList } from "@/components/Orders"
import { toaster } from "@/components/ui/toaster"

const STORAGE_KEY = "dashboard_selected_orders"

export const Route = createFileRoute("/_layout/")({
  component: Dashboard,
})

function Dashboard() {
  const { user: currentUser } = useAuth()

  // Initialize from sessionStorage
  const [selectedOrderIds, setSelectedOrderIds] = useState<number[]>(() => {
    try {
      const stored = sessionStorage.getItem(STORAGE_KEY)
      return stored ? JSON.parse(stored) : []
    } catch {
      return []
    }
  })

  // Persist to sessionStorage whenever it changes
  useEffect(() => {
    if (selectedOrderIds.length > 0) {
      sessionStorage.setItem(STORAGE_KEY, JSON.stringify(selectedOrderIds))
    } else {
      sessionStorage.removeItem(STORAGE_KEY)
    }
  }, [selectedOrderIds])

  const {
    data: orders,
    isLoading,
    error,
  } = useOrdersBulk(selectedOrderIds)

  const handleOrdersSelected = (orderIds: number[]) => {
    const previousCount = selectedOrderIds.length
    const newCount = orderIds.length
    const addedCount = newCount - previousCount

    setSelectedOrderIds(orderIds)

    // Only show toast when adding orders (not when removing)
    if (addedCount > 0) {
      toaster.create({
        title: "Loading order",
        description: `Fetching order ${orderIds[orderIds.length - 1]} from MIRA...`,
        type: "info",
      })
    }
  }

  // Show error toast if query fails
  useEffect(() => {
    if (error) {
      toaster.create({
        title: "Error loading orders",
        description: error.message || "Failed to fetch order information from MIRA",
        type: "error",
      })
    }
  }, [error])

  return (
    <Container maxW="container.xl" py={12}>
      <Stack gap={8}>
        {/* Header */}
        <Stack gap={2}>
          <Heading size="2xl">
            Hi, {currentUser?.full_name || currentUser?.email} 👋
          </Heading>
          <Text color="gray.600">
            Welcome back! Load orders from MIRA to view device information for measurements.
          </Text>
        </Stack>

        {/* Order Selector */}
        <OrderSelector
          onOrdersSelected={handleOrdersSelected}
          initialOrderIds={selectedOrderIds}
          maxOrders={4}
        />

        {/* Device List */}
        <DeviceList orders={orders || []} isLoading={isLoading} />
      </Stack>
    </Container>
  )
}
