from dataclasses import dataclass


@dataclass
class CreateUserRequest:
    email: str
    full_name: str
    home_currency: str = "USD"
