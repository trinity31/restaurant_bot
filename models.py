from typing import Optional

from pydantic import BaseModel


class RestaurantCustomerContext(BaseModel):
    customer_id: int
    name: str
    phone: Optional[str] = None
    preferred_language: str = "ko"


class InputGuardRailOutput(BaseModel):
    is_off_topic: bool
    has_inappropriate_language: bool
    reason: str


class RestaurantOutputGuardRailOutput(BaseModel):
    lacks_professional_tone: bool
    contains_internal_info: bool
    reason: str


class HandoffData(BaseModel):
    to_agent_name: str
    intent: str
    reason: str
    user_request: str
