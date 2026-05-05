from pydantic import BaseModel, field_validator

class LoginSchema(BaseModel):
    email: str
    password: str

    @field_validator("email", mode="before")
    @classmethod
    def validate_email(cls, value: str) -> str:
        return value.strip().lower()


class CustomerLoginSchema(BaseModel):
    phone_number: str
    location_text: str | None = None
    location_lat: float | None = None
    location_lng: float | None = None

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, value: str) -> str:
        normalized = value.strip()
        if len(normalized) < 7:
            raise ValueError("Telefon raqami noto'g'ri")
        return normalized

    @field_validator("location_text")
    @classmethod
    def validate_location_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = " ".join(value.strip().split())
        return normalized or None


class CustomerRegisterSchema(CustomerLoginSchema):
    full_name: str

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, value: str) -> str:
        normalized = value.strip()
        if len(normalized) < 3:
            raise ValueError("To'liq ism kamida 3 ta belgi bo'lishi kerak")
        return normalized


CustomerAuthSchema = CustomerRegisterSchema


class RefreshSchema(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str | None = None
    token_type: str = "bearer"
