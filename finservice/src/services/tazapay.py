import base64
import logging

import aiohttp

from src.core.settings import settings
from src.schemas.payment_service import TazapayServiceRequest

from src.schemas.payment_service import TazapayServiceResponse

logger = logging.getLogger(__name__)

class TazapayService:

    def __init__(self):
        self.api_url = settings.TAZAPAY_PAYOUT_ENDPOINT
        self.auth = aiohttp.BasicAuth(
            login=settings.TAZAPAY_API_KEY,
            password=settings.TAZAPAY_API_SECRET,
        )


    async def run_payout(self, payload:dict) ->TazapayServiceResponse:
        logger.info("Initiating Tazapay payment request")
        logger.debug(f"Tazapay payment payload: {payload}")
        request_data = payload.model_dump(
            by_alias=True,
            exclude_none=True,
        )

        logger.info(
            "Tazapay request payload: %s",
            request_data,
        )
        try:
            async with aiohttp.ClientSession(auth=self.auth) as session:
                request_data = payload.model_dump(
                    by_alias=True,
                    exclude_none=True,
                )

                logger.info(
                    "Tazapay request payload: %s",
                    request_data,
                )
                async with session.post(self.api_url,json=payload.model_dump(by_alias=True, exclude_none=True)) as response:
                    logger.info(f"Tazapay payment response received. Status: {response.status}" )
                    response_data = await response.json()
                    if response.status >= 400:
                        logger.error(
                            "Tazapay API error: status=%s response=%s",
                            response.status,
                            response_data,
                        )
                    response.raise_for_status()
                    logger.info("Payout request successful..")
                    return TazapayServiceResponse.model_validate(response_data)

        except aiohttp.ClientResponseError as exc:
            logger.error(
                "Tazapay payment request failed: status=%s, message=%s",
                exc.status,
                exc.message,
            )
            raise

        except aiohttp.ClientError:
            logger.exception(
                "Tazapay payment request failed due to an HTTP client error"
            )
            raise

        except Exception:
            logger.exception(
                "Unexpected error while processing Tazapay payment"
            )
            raise
