import logging
from google.cloud import storage

logger = logging.getLogger(__name__)


class GCSDriver:
    def __init__(self, project_id: str, bucket_name: str):
        self.project_id = project_id
        self.bucket_name = bucket_name
        self.storage_client = storage.Client(project=self.project_id)
        self.bucket = self.storage_client.bucket(self.bucket_name)

    def upload_blob(self, blob_name: str, content: str):
        try:
            # Ensure the bucket exists
            if not self.bucket.exists():
                raise ValueError(f"Bucket {self.bucket_name} does not exist.")
            logger.info(f"Uploading blob {blob_name} to GCS bucket {self.bucket_name}")
            blob = self.bucket.blob(blob_name)
            blob.upload_from_string(content, content_type="text/csv")
            logger.info(f"Uploaded blob {blob_name} to GCS bucket {self.bucket_name}")
            return blob_name
        except Exception as e:
            logger.error(
                f"Failed to upload blob {blob_name} to GCS bucket {self.bucket_name}: {str(e)}"
            )
            raise RuntimeError(f"Failed to upload blob {blob_name}: {str(e)}")
