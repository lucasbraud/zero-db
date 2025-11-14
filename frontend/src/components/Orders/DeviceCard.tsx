import { useState } from "react"
import {
  Box,
  Card,
  Grid,
  GridItem,
  Heading,
  Image,
  Stack,
  Text,
} from "@chakra-ui/react"
import {
  DialogActionTrigger,
  DialogBody,
  DialogCloseTrigger,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogRoot,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import type { DeviceWithPicture } from "@/client"

interface DeviceCardProps {
  device: DeviceWithPicture
  index: number
}

export function DeviceCard({ device, index }: DeviceCardProps) {
  const [open, setOpen] = useState(false)
  const [imageError, setImageError] = useState(false)

  const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000"
  const thumbnailUrl = device.picture_url ? `${apiUrl}${device.picture_url}?thumbnail=true` : ""
  const fullImageUrl = device.picture_url ? `${apiUrl}${device.picture_url}` : ""

  return (
    <DialogRoot open={open} onOpenChange={(e) => setOpen(e.open)}>
      <Card.Root
        variant="outline"
        _hover={{ shadow: "md", borderColor: "blue.300" }}
        transition="all 0.2s"
      >
        <Card.Body>
          <Stack gap={3}>
            {/* Device Header */}
            <Box>
              <Text fontSize="sm" color="gray.500">
                Device {index + 1}
              </Text>
              <Heading size="md">{device.waveguide_name}</Heading>
              <Text fontSize="xs" color="gray.600" mt={1}>
                ID: {device.comb_placed_id}
              </Text>
            </Box>

            {/* Thumbnail Image */}
            <DialogTrigger asChild>
              <Box
                cursor="pointer"
                borderRadius="md"
                overflow="hidden"
                borderWidth="1px"
                borderColor="gray.200"
                bg="gray.50"
                _hover={{ borderColor: "blue.400" }}
                transition="border-color 0.2s"
              >
                {imageError ? (
                  <Box
                    h="200px"
                    display="flex"
                    alignItems="center"
                    justifyContent="center"
                    bg="gray.100"
                  >
                    <Text color="gray.500" fontSize="sm">
                      Image unavailable
                    </Text>
                  </Box>
                ) : (
                  <Image
                    src={thumbnailUrl}
                    alt={`Device ${device.waveguide_name}`}
                    width="full"
                    height="200px"
                    objectFit="contain"
                    onError={() => setImageError(true)}
                  />
                )}
              </Box>
            </DialogTrigger>

            {/* Position Information */}
            <Grid templateColumns="repeat(2, 1fr)" gap={2} fontSize="xs">
              <GridItem>
                <Text fontWeight="medium" color="gray.700">
                  Input Position
                </Text>
                <Text color="gray.600">
                  X: {device.input_port_position.position_x_um.toFixed(1)} μm
                </Text>
                <Text color="gray.600">
                  Y: {device.input_port_position.position_y_um.toFixed(1)} μm
                </Text>
              </GridItem>
              <GridItem>
                <Text fontWeight="medium" color="gray.700">
                  Output Position
                </Text>
                <Text color="gray.600">
                  X: {device.output_port_position.position_x_um.toFixed(1)} μm
                </Text>
                <Text color="gray.600">
                  Y: {device.output_port_position.position_y_um.toFixed(1)} μm
                </Text>
              </GridItem>
            </Grid>
          </Stack>
        </Card.Body>
      </Card.Root>

      {/* Full Image Dialog */}
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{device.waveguide_name}</DialogTitle>
          <DialogCloseTrigger />
        </DialogHeader>
        <DialogBody>
          <Stack gap={4}>
            {/* Full-size Image */}
            <Box
              borderRadius="md"
              overflow="hidden"
              borderWidth="1px"
              borderColor="gray.200"
              bg="gray.50"
            >
              {imageError ? (
                <Box
                  h="400px"
                  display="flex"
                  alignItems="center"
                  justifyContent="center"
                  bg="gray.100"
                >
                  <Text color="gray.500">Image unavailable</Text>
                </Box>
              ) : (
                <Image
                  src={fullImageUrl}
                  alt={`Device ${device.waveguide_name} full view`}
                  width="full"
                  maxHeight="500px"
                  objectFit="contain"
                  onError={() => setImageError(true)}
                />
              )}
            </Box>

            {/* Detailed Information */}
            <Grid templateColumns="repeat(2, 1fr)" gap={4}>
              <GridItem>
                <Text fontSize="sm" fontWeight="medium" mb={2}>
                  Device Details
                </Text>
                <Stack gap={1} fontSize="sm">
                  <Text color="gray.600">
                    <strong>ID:</strong> {device.comb_placed_id}
                  </Text>
                  <Text color="gray.600">
                    <strong>Name:</strong> {device.waveguide_name}
                  </Text>
                  <Text color="gray.600">
                    <strong>Connector:</strong> {device.devices_set_connector_id}
                  </Text>
                </Stack>
              </GridItem>

              <GridItem>
                <Text fontSize="sm" fontWeight="medium" mb={2}>
                  Geometry
                </Text>
                {device.geometry ? (
                  <Stack gap={1} fontSize="sm">
                    {device.geometry.coupling_length_um !== null && device.geometry.coupling_length_um !== undefined && (
                      <Text color="gray.600">
                        <strong>Coupling Length:</strong> {device.geometry.coupling_length_um.toFixed(1)} μm
                      </Text>
                    )}
                    {device.geometry.ring_radius_um !== null && device.geometry.ring_radius_um !== undefined && (
                      <Text color="gray.600">
                        <strong>Ring Radius:</strong> {device.geometry.ring_radius_um.toFixed(1)} μm
                      </Text>
                    )}
                    {device.geometry.gap_um !== null && device.geometry.gap_um !== undefined && (
                      <Text color="gray.600">
                        <strong>Gap:</strong> {device.geometry.gap_um.toFixed(1)} μm
                      </Text>
                    )}
                    {device.geometry.bus_width_um !== null && device.geometry.bus_width_um !== undefined && (
                      <Text color="gray.600">
                        <strong>Bus Width:</strong> {device.geometry.bus_width_um.toFixed(1)} μm
                      </Text>
                    )}
                  </Stack>
                ) : (
                  <Text color="gray.500" fontSize="sm">
                    No geometry data
                  </Text>
                )}
              </GridItem>

              <GridItem colSpan={2}>
                <Text fontSize="sm" fontWeight="medium" mb={2}>
                  Port Positions
                </Text>
                <Grid templateColumns="repeat(2, 1fr)" gap={3} fontSize="sm">
                  <Box>
                    <Text fontWeight="medium" color="gray.700">
                      Input Port
                    </Text>
                    <Text color="gray.600">
                      X: {device.input_port_position.position_x_um.toFixed(2)} μm
                    </Text>
                    <Text color="gray.600">
                      Y: {device.input_port_position.position_y_um.toFixed(2)} μm
                    </Text>
                  </Box>
                  <Box>
                    <Text fontWeight="medium" color="gray.700">
                      Output Port
                    </Text>
                    <Text color="gray.600">
                      X: {device.output_port_position.position_x_um.toFixed(2)} μm
                    </Text>
                    <Text color="gray.600">
                      Y: {device.output_port_position.position_y_um.toFixed(2)} μm
                    </Text>
                  </Box>
                </Grid>
              </GridItem>
            </Grid>
          </Stack>
        </DialogBody>
        <DialogFooter>
          <DialogActionTrigger asChild>
            <Button variant="outline">Close</Button>
          </DialogActionTrigger>
        </DialogFooter>
      </DialogContent>
    </DialogRoot>
  )
}
