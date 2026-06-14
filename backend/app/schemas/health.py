from pydantic import BaseModel


class HealthGetResponse(BaseModel):
  message: str
