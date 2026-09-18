from enum import Enum

class PaymentStatus(Enum):
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"
