import {
  Box,
  Card,
  Grid,
  Heading,
  Spinner,
  Stack,
  Text,
} from "@chakra-ui/react"
import { Tabs } from "@chakra-ui/react"
import type { OrderInfoResponse } from "@/client"
import { DeviceCard } from "./DeviceCard"

interface DeviceListProps {
  orders: OrderInfoResponse[]
  isLoading?: boolean
}

export function DeviceList({ orders, isLoading = false }: DeviceListProps) {
  if (isLoading) {
    return (
      <Card.Root>
        <Card.Body>
          <Stack align="center" gap={4} py={8}>
            <Spinner size="xl" colorPalette="blue" />
            <Text color="gray.600">Loading order information...</Text>
          </Stack>
        </Card.Body>
      </Card.Root>
    )
  }

  if (!orders || orders.length === 0) {
    return (
      <Card.Root>
        <Card.Body>
          <Stack align="center" gap={4} py={8}>
            <Text color="gray.600">No orders selected</Text>
            <Text fontSize="sm" color="gray.500">
              Use the order selector above to load device information
            </Text>
          </Stack>
        </Card.Body>
      </Card.Root>
    )
  }

  // Single order - no tabs needed
  if (orders.length === 1) {
    const order = orders[0]
    return (
      <Stack gap={6}>
        {/* Order Header */}
        <Card.Root>
          <Card.Header>
            <Heading size="lg">
              Order #{order.order_id}
              {order.order_name && ` - ${order.order_name}`}
            </Heading>
            <Text color="gray.600" fontSize="sm" mt={2}>
              {order.devices.length} device{order.devices.length !== 1 ? "s" : ""}
            </Text>
          </Card.Header>

          {/* Measurement Parameters */}
          {order.measurement_parameters && (
            <Card.Body borderTopWidth="1px">
              <Text fontSize="sm" fontWeight="medium" mb={3}>
                Measurement Parameters
              </Text>
              <Grid templateColumns="repeat(auto-fit, minmax(200px, 1fr))" gap={3}>
                <Box>
                  <Text fontSize="xs" color="gray.600">
                    Laser Power
                  </Text>
                  <Text fontWeight="medium">
                    {order.measurement_parameters.laser_power_db} dB
                  </Text>
                </Box>
                <Box>
                  <Text fontSize="xs" color="gray.600">
                    Sweep Speed
                  </Text>
                  <Text fontWeight="medium">
                    {order.measurement_parameters.sweep_speed} nm/s
                  </Text>
                </Box>
                <Box>
                  <Text fontSize="xs" color="gray.600">
                    Wavelength Range
                  </Text>
                  <Text fontWeight="medium">
                    {order.measurement_parameters.start_wl_nm} -{" "}
                    {order.measurement_parameters.stop_wl_nm} nm
                  </Text>
                </Box>
                <Box>
                  <Text fontSize="xs" color="gray.600">
                    Resolution
                  </Text>
                  <Text fontWeight="medium">
                    {order.measurement_parameters.resolution_nm} nm
                  </Text>
                </Box>
              </Grid>
            </Card.Body>
          )}
        </Card.Root>

        {/* Devices Grid */}
        <Grid
          templateColumns={{
            base: "1fr",
            md: "repeat(2, 1fr)",
            lg: "repeat(3, 1fr)",
          }}
          gap={4}
        >
          {order.devices.map((device, index) => (
            <DeviceCard key={device.comb_placed_id} device={device} index={index} />
          ))}
        </Grid>
      </Stack>
    )
  }

  // Multiple orders - use tabs
  return (
    <Tabs.Root defaultValue={`order-${orders[0].order_id}`}>
      <Tabs.List>
        {orders.map((order) => (
          <Tabs.Trigger key={order.order_id} value={`order-${order.order_id}`}>
            Order #{order.order_id}
            <Text as="span" fontSize="xs" color="gray.500" ml={2}>
              ({order.devices.length})
            </Text>
          </Tabs.Trigger>
        ))}
      </Tabs.List>

      {orders.map((order) => (
        <Tabs.Content key={order.order_id} value={`order-${order.order_id}`}>
          <Stack gap={6} pt={4}>
            {/* Order Header */}
            <Card.Root>
              <Card.Header>
                <Heading size="lg">
                  Order #{order.order_id}
                  {order.order_name && ` - ${order.order_name}`}
                </Heading>
                <Text color="gray.600" fontSize="sm" mt={2}>
                  {order.devices.length} device{order.devices.length !== 1 ? "s" : ""}
                </Text>
              </Card.Header>

              {/* Measurement Parameters */}
              {order.measurement_parameters && (
                <Card.Body borderTopWidth="1px">
                  <Text fontSize="sm" fontWeight="medium" mb={3}>
                    Measurement Parameters
                  </Text>
                  <Grid templateColumns="repeat(auto-fit, minmax(200px, 1fr))" gap={3}>
                    <Box>
                      <Text fontSize="xs" color="gray.600">
                        Laser Power
                      </Text>
                      <Text fontWeight="medium">
                        {order.measurement_parameters.laser_power_db} dB
                      </Text>
                    </Box>
                    <Box>
                      <Text fontSize="xs" color="gray.600">
                        Sweep Speed
                      </Text>
                      <Text fontWeight="medium">
                        {order.measurement_parameters.sweep_speed} nm/s
                      </Text>
                    </Box>
                    <Box>
                      <Text fontSize="xs" color="gray.600">
                        Wavelength Range
                      </Text>
                      <Text fontWeight="medium">
                        {order.measurement_parameters.start_wl_nm} -{" "}
                        {order.measurement_parameters.stop_wl_nm} nm
                      </Text>
                    </Box>
                    <Box>
                      <Text fontSize="xs" color="gray.600">
                        Resolution
                      </Text>
                      <Text fontWeight="medium">
                        {order.measurement_parameters.resolution_nm} nm
                      </Text>
                    </Box>
                  </Grid>
                </Card.Body>
              )}
            </Card.Root>

            {/* Devices Grid */}
            <Grid
              templateColumns={{
                base: "1fr",
                md: "repeat(2, 1fr)",
                lg: "repeat(3, 1fr)",
              }}
              gap={4}
            >
              {order.devices.map((device, index) => (
                <DeviceCard
                  key={device.comb_placed_id}
                  device={device}
                  index={index}
                />
              ))}
            </Grid>
          </Stack>
        </Tabs.Content>
      ))}
    </Tabs.Root>
  )
}
