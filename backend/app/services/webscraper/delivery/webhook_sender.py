"""
Webhook Sender

This module sends extraction results to webhooks/APIs.
"""

import logging
import os
from typing import Dict, Any, Optional
from datetime import datetime
import httpx

logger = logging.getLogger(__name__)


class WebhookSender:
    """Send files or data to webhooks"""

    def __init__(self, timeout: int = 30):
        """
        Initialize webhook sender

        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout

    async def deliver(
        self,
        file_path: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Send file to webhook

        Args:
            file_path: Path to file to send
            config: Delivery configuration with keys:
                - url: Webhook URL (required)
                - method: HTTP method (GET, POST, PUT, default: POST)
                - headers: Custom headers (optional)
                - send_as: How to send ('file', 'json', 'data')
                - metadata: Additional metadata to send

        Returns:
            Delivery result
        """
        logger.info(f"Sending to webhook: {file_path}")

        try:
            # Validate configuration
            webhook_url = config.get('url')
            if not webhook_url:
                raise ValueError("Webhook 'url' is required")

            method = config.get('method', 'POST').upper()
            headers = config.get('headers', {})
            send_as = config.get('send_as', 'file')

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                if send_as == 'file':
                    # Send as file upload
                    if not os.path.exists(file_path):
                        raise FileNotFoundError(f"File not found: {file_path}")

                    with open(file_path, 'rb') as f:
                        files = {'file': (os.path.basename(file_path), f)}

                        if method == 'POST':
                            response = await client.post(
                                webhook_url,
                                files=files,
                                headers=headers
                            )
                        elif method == 'PUT':
                            response = await client.put(
                                webhook_url,
                                files=files,
                                headers=headers
                            )
                        else:
                            raise ValueError(f"Unsupported method for file upload: {method}")

                elif send_as == 'json':
                    # Send file contents as JSON
                    import pandas as pd

                    # Read file and convert to JSON
                    if file_path.endswith('.csv'):
                        df = pd.read_csv(file_path)
                    elif file_path.endswith(('.xlsx', '.xls')):
                        df = pd.read_excel(file_path)
                    elif file_path.endswith('.json'):
                        df = pd.read_json(file_path)
                    else:
                        raise ValueError(f"Unsupported file type for JSON conversion: {file_path}")

                    data = df.to_dict(orient='records')

                    # Add metadata if provided
                    payload = {
                        'data': data,
                        'metadata': config.get('metadata', {})
                    }

                    if method == 'POST':
                        response = await client.post(
                            webhook_url,
                            json=payload,
                            headers=headers
                        )
                    elif method == 'PUT':
                        response = await client.put(
                            webhook_url,
                            json=payload,
                            headers=headers
                        )
                    else:
                        response = await client.get(
                            webhook_url,
                            params=payload,
                            headers=headers
                        )

                else:
                    raise ValueError(f"Unsupported send_as value: {send_as}")

                # Check response
                response.raise_for_status()

                logger.info(
                    f"Webhook delivery successful: {response.status_code} from {webhook_url}"
                )

                return {
                    'success': True,
                    'method': 'webhook',
                    'destination': webhook_url,
                    'delivered_at': datetime.utcnow(),
                    'error': None,
                    'metadata': {
                        'status_code': response.status_code,
                        'response_body': response.text[:500]  # First 500 chars
                    }
                }

        except Exception as e:
            logger.error(f"Error sending to webhook: {str(e)}")
            return {
                'success': False,
                'method': 'webhook',
                'destination': config.get('url', 'unknown'),
                'delivered_at': None,
                'error': str(e),
                'metadata': {}
            }


# Export
__all__ = ['WebhookSender']
