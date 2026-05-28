"""Shared domain models. Plain dataclasses — services may wrap with Pydantic."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from enum import Enum

from travel_common.currency import Currency


class BookingStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class TripType(str, Enum):
    FLIGHT = "flight"
    HOTEL = "hotel"
    CAR = "car"
    PACKAGE = "package"


@dataclass(frozen=True)
class Money:
    amount: Decimal
    currency: Currency


@dataclass(frozen=True)
class Address:
    line1: str
    city: str
    country: str
    postal_code: str
    line2: str | None = None
    region: str | None = None


@dataclass
class Passenger:
    first_name: str
    last_name: str
    date_of_birth: date
    passport_number: str | None = None
    loyalty_id: str | None = None


@dataclass
class User:
    id: str
    email: str
    full_name: str
    home_currency: Currency = Currency.USD
    address: Address | None = None
    loyalty_tier: str | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Itinerary:
    id: str
    trip_type: TripType
    origin: str
    destination: str
    depart_at: datetime
    return_at: datetime | None
    base_price: Money


@dataclass
class Booking:
    id: str
    user_id: str
    itinerary: Itinerary
    passengers: list[Passenger]
    status: BookingStatus
    total: Money
    created_at: datetime = field(default_factory=datetime.utcnow)
