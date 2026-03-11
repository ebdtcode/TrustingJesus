"""Azure Blob Storage helpers for audio staging.

The GitHub Action downloads audio from YouTube (where yt-dlp works)
and uploads it to blob storage. The Azure Function then reads from blob
for transcription and processing.
"""

from __future__ import annotations

import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

CONTAINER_NAME = "sermon-audio"


def download_blob_to_file(blob_name: str, dest_path: str) -> str:
    """Download a blob to a local file path.

    Uses the function app's AzureWebJobsStorage connection string.
    """
    from azure.storage.blob import BlobServiceClient

    conn_str = os.environ.get("AzureWebJobsStorage", "")
    if not conn_str:
        raise ValueError("AzureWebJobsStorage connection string not configured")

    blob_service = BlobServiceClient.from_connection_string(conn_str)
    blob_client = blob_service.get_blob_client(CONTAINER_NAME, blob_name)

    logger.info("Downloading blob %s/%s to %s", CONTAINER_NAME, blob_name, dest_path)
    with open(dest_path, "wb") as f:
        stream = blob_client.download_blob()
        stream.readinto(f)

    size_mb = os.path.getsize(dest_path) / (1024 * 1024)
    logger.info("Downloaded %.1f MB from blob", size_mb)
    return dest_path


def delete_blob(blob_name: str) -> None:
    """Delete a blob after processing (cleanup)."""
    from azure.storage.blob import BlobServiceClient

    conn_str = os.environ.get("AzureWebJobsStorage", "")
    if not conn_str:
        return

    try:
        blob_service = BlobServiceClient.from_connection_string(conn_str)
        blob_client = blob_service.get_blob_client(CONTAINER_NAME, blob_name)
        blob_client.delete_blob()
        logger.info("Deleted blob %s/%s", CONTAINER_NAME, blob_name)
    except Exception as e:
        logger.warning("Failed to delete blob %s: %s", blob_name, e)
