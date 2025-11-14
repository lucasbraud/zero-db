import { useState, useEffect, type ChangeEvent, type KeyboardEvent } from "react"
import {
  Box,
  Button,
  Card,
  Fieldset,
  HStack,
  Heading,
  Input,
  Stack,
  Text,
  For,
} from "@chakra-ui/react"
import { CloseButton } from "@/components/ui/close-button"

interface OrderSelectorProps {
  onOrdersSelected: (orderIds: number[]) => void
  initialOrderIds?: number[]
  maxOrders?: number
}

export function OrderSelector({
  onOrdersSelected,
  initialOrderIds = [],
  maxOrders = 4,
}: OrderSelectorProps) {
  const [orderIds, setOrderIds] = useState<number[]>(initialOrderIds)

  // Sync with initialOrderIds when they change (e.g., from URL)
  useEffect(() => {
    setOrderIds(initialOrderIds)
  }, [initialOrderIds])
  const [inputValue, setInputValue] = useState("")
  const [error, setError] = useState("")

  const handleInputChange = (e: ChangeEvent<HTMLInputElement>) => {
    setInputValue(e.target.value)
    setError("")
  }

  const handleAddOrder = () => {
    const orderId = parseInt(inputValue.trim())

    // Validation
    if (!inputValue.trim()) {
      setError("Please enter an order ID")
      return
    }

    if (isNaN(orderId) || orderId <= 0) {
      setError("Order ID must be a positive number")
      return
    }

    if (orderIds.includes(orderId)) {
      setError("This order ID is already added")
      return
    }

    if (orderIds.length >= maxOrders) {
      setError(`Maximum ${maxOrders} orders allowed`)
      return
    }

    // Add order
    setOrderIds([...orderIds, orderId])
    setInputValue("")
    setError("")
  }

  const handleRemoveOrder = (orderId: number) => {
    const updatedOrderIds = orderIds.filter((id) => id !== orderId)
    setOrderIds(updatedOrderIds)
    setError("")
    // Immediately update parent component to remove the order
    onOrdersSelected(updatedOrderIds)
  }

  const handleKeyPress = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      handleAddOrder()
    }
  }

  const handleLoadOrders = () => {
    if (orderIds.length === 0) {
      setError("Please add at least one order ID")
      return
    }
    onOrdersSelected(orderIds)
  }

  return (
    <Card.Root>
      <Card.Header>
        <Heading size="lg">Select Orders</Heading>
        <Text color="gray.600" fontSize="sm" mt={2}>
          Enter order IDs to load device information (max {maxOrders} orders for
          multi-chip measurements)
        </Text>
      </Card.Header>

      <Card.Body>
        <Stack gap={4} align="stretch">
          {/* Input Section */}
          <Fieldset.Root invalid={!!error}>
            <Fieldset.Legend>Order ID</Fieldset.Legend>
            <HStack>
              <Input
                type="number"
                min={1}
                placeholder="Enter order ID (e.g., 280)"
                value={inputValue}
                onChange={handleInputChange}
                onKeyPress={handleKeyPress}
                disabled={orderIds.length >= maxOrders}
              />
              <Button
                onClick={handleAddOrder}
                colorPalette="blue"
                disabled={orderIds.length >= maxOrders}
              >
                Add
              </Button>
            </HStack>
            {error && <Fieldset.ErrorText>{error}</Fieldset.ErrorText>}
          </Fieldset.Root>

          {/* Selected Orders */}
          {orderIds.length > 0 && (
            <Box>
              <Text fontSize="sm" fontWeight="medium" mb={2}>
                Selected Orders ({orderIds.length}/{maxOrders})
              </Text>
              <Stack gap={2}>
                <For each={orderIds}>
                  {(orderId) => (
                    <HStack
                      key={orderId}
                      p={3}
                      borderWidth="1px"
                      borderRadius="md"
                      justify="space-between"
                      bg="blue.50"
                      borderColor="blue.200"
                    >
                      <Text fontWeight="medium">Order #{orderId}</Text>
                      <CloseButton
                        size="sm"
                        onClick={() => handleRemoveOrder(orderId)}
                        aria-label={`Remove order ${orderId}`}
                      />
                    </HStack>
                  )}
                </For>
              </Stack>
            </Box>
          )}

          {/* Load Button */}
          <Button
            onClick={handleLoadOrders}
            colorPalette="green"
            size="lg"
            disabled={orderIds.length === 0}
            width="full"
          >
            Load {orderIds.length} Order{orderIds.length !== 1 ? "s" : ""}
          </Button>
        </Stack>
      </Card.Body>
    </Card.Root>
  )
}
