"""
Delivery Factory

This module provides a factory for creating delivery handlers based on method.
"""

import logging
from typing import Dict, Any, Type

from .download_handler import DownloadHandler
from .email_sender import EmailSender
from .webhook_sender import WebhookSender
from .storage_uploader import StorageUploader

logger = logging.getLogger(__name__)


class DeliveryFactory:
    """
    Factory for creating delivery handlers

    Provides a centralized way to get the appropriate delivery handler
    based on the requested delivery method.
    """

    # Registry of delivery handlers
    _handlers: Dict[str, Type] = {
        'download': DownloadHandler,
        'email': EmailSender,
        'webhook': WebhookSender,
        'storage': StorageUploader,
        's3': StorageUploader,
        'minio': StorageUploader,
        'gcs': StorageUploader,
        'azure': StorageUploader
    }

    @classmethod
    def create(cls, delivery_method: str):
        """
        Create delivery handler for specified method

        Args:
            delivery_method: Delivery method (download, email, webhook, storage, etc.)

        Returns:
            Delivery handler instance

        Raises:
            ValueError: If method is not supported
        """
        delivery_method = delivery_method.lower()

        handler_class = cls._handlers.get(delivery_method)

        if handler_class is None:
            supported_methods = ', '.join(set(cls._handlers.keys()))
            raise ValueError(
                f"Unsupported delivery method '{delivery_method}'. "
                f"Supported methods: {supported_methods}"
            )

        logger.debug(
            f"Creating {handler_class.__name__} for method '{delivery_method}'"
        )
        return handler_class()

    @classmethod
    def get_supported_methods(cls) -> list:
        """
        Get list of supported delivery methods

        Returns:
            List of method names
        """
        return list(set(cls._handlers.keys()))

    @classmethod
    def register_handler(cls, method_name: str, handler_class: Type):
        """
        Register a custom delivery handler

        Args:
            method_name: Name of the delivery method
            handler_class: Handler class
        """
        cls._handlers[method_name.lower()] = handler_class
        logger.info(f"Registered custom handler for method '{method_name}'")


# Export
__all__ = ['DeliveryFactory']
