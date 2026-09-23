from pydantic import BaseModel

class WebhookData(BaseModel):
    id: str
    status: str


class TazapayWebhook(BaseModel):
    type: str
    data: WebhookData
