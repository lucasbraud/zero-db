import uuid

from pydantic import EmailStr
from sqlmodel import Field, Relationship, SQLModel


# Shared properties
class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)


class UserRegister(SQLModel):
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on update, all are optional
class UserUpdate(UserBase):
    email: EmailStr | None = Field(default=None, max_length=255)  # type: ignore
    password: str | None = Field(default=None, min_length=8, max_length=128)


class UserUpdateMe(SQLModel):
    full_name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = Field(default=None, max_length=255)


class UpdatePassword(SQLModel):
    current_password: str = Field(min_length=8, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


# Database model, database table inferred from class name
class User(UserBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str
    items: list["Item"] = Relationship(back_populates="owner", cascade_delete=True)


# Properties to return via API, id is always required
class UserPublic(UserBase):
    id: uuid.UUID


class UsersPublic(SQLModel):
    data: list[UserPublic]
    count: int


# Shared properties
class ItemBase(SQLModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)


# Properties to receive on item creation
class ItemCreate(ItemBase):
    pass


# Properties to receive on item update
class ItemUpdate(ItemBase):
    title: str | None = Field(default=None, min_length=1, max_length=255)  # type: ignore


# Database model, database table inferred from class name
class Item(ItemBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE"
    )
    owner: User | None = Relationship(back_populates="items")


# Properties to return via API, id is always required
class ItemPublic(ItemBase):
    id: uuid.UUID
    owner_id: uuid.UUID


class ItemsPublic(SQLModel):
    data: list[ItemPublic]
    count: int


# Generic message
class Message(SQLModel):
    message: str


# MIRA Database Models
# These are not database tables, but Pydantic models for API I/O


class DevicePosition(SQLModel):
    """Device port position in micrometers."""

    position_x_um: float
    position_y_um: float
    position_z_um: float | None = None


class DeviceGeometry(SQLModel):
    """Device geometry parameters."""

    gap_um: float | None = None
    bus_width_um: float | None = None
    coupling_length_um: float | None = None
    ring_radius_um: float | None = None
    # Add more geometry fields as needed


class Device(SQLModel):
    """Device information from MIRA order."""

    comb_placed_id: int
    waveguide_name: str
    devices_set_connector_id: int
    input_port_position: DevicePosition
    output_port_position: DevicePosition
    geometry: DeviceGeometry | None = None


class DeviceWithPicture(Device):
    """Device with picture URL."""

    picture_url: str | None = None


class MeasurementParameters(SQLModel):
    """Measurement configuration parameters."""

    laser_power_db: float
    sweep_speed: int
    start_wl_nm: float
    stop_wl_nm: float
    resolution_nm: float


class OrderInfo(SQLModel):
    """Order information from MIRA."""

    order_id: int
    order_name: str | None = None
    devices: list[Device]
    measurement_parameters: MeasurementParameters
    calibrated_setup_id: int | None = None


class OrderInfoResponse(SQLModel):
    """Order info response with picture URLs."""

    order_id: int
    order_name: str | None = None
    devices: list[DeviceWithPicture]
    measurement_parameters: MeasurementParameters | None = None
    calibrated_setup_id: int | None = None


class OrderBulkRequest(SQLModel):
    """Request for multiple orders (multi-chip measurements)."""

    order_ids: list[int] = Field(min_length=1, max_length=4)


# JSON payload containing access token
class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


# Contents of JWT token
class TokenPayload(SQLModel):
    sub: str | None = None


class NewPassword(SQLModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)
