/**
 * MIRA Database Types
 *
 * Types for orders, devices, and measurement parameters from MIRA API.
 */

export interface DevicePosition {
  position_x_um: number
  position_y_um: number
  position_z_um?: number
}

export interface DeviceGeometry {
  gap_um?: number
  bus_width_um?: number
  coupling_length_um?: number
  ring_radius_um?: number
}

export interface Device {
  comb_placed_id: number
  waveguide_name: string
  devices_set_connector_id: number
  input_port_position: DevicePosition
  output_port_position: DevicePosition
  geometry?: DeviceGeometry
}

export interface DeviceWithPicture extends Device {
  picture_url?: string
}

export interface MeasurementParameters {
  laser_power_db: number
  sweep_speed: number
  start_wl_nm: number
  stop_wl_nm: number
  resolution_nm: number
}

export interface OrderInfo {
  order_id: number
  order_name?: string
  devices: DeviceWithPicture[]
  measurement_parameters: MeasurementParameters
  calibrated_setup_id?: number
}

export interface OrderBulkRequest {
  order_ids: number[]
}
