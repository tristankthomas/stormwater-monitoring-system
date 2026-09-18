from pydantic import BaseModel


class SensorReading(BaseModel):
    timestamp: int
    turbidity: float
    conductivity: float
    diverter_active: bool


class LivePayload(BaseModel):
    timestamp: int
    turbidity: float
    conductivity: float
    diverter_active: bool
    pollution_score: str
    rain_event: bool


class Event(BaseModel):
    timestamp: int
    event_type: str
    message: str
