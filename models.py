from pydantic import BaseModel
from typing import List, Optional


class Observation(BaseModel):
    ticket_id: str
    customer_query: str
    customer_id: str
    order_id: Optional[str] = None
    previous_actions: List[str] = []
    available_tools: List[str] = []
    system_messages: List[str] = []


class Action(BaseModel):
    tool_name: str
    parameters: dict


class Reward(BaseModel):
    score: float
    reason: str