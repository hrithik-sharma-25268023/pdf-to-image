"""Read and write files to S3"""

import boto3


class FileSystem:
    """file system class"""

    def __init__(self, s3_client: boto3.client) -> None:
        self.s3_client = s3_client


    def read_png(self, bucket: str, key: str) -> bytes:
        """Read PNG file from S3 and return as bytes"""

        response = self.s3_client.get_object(Bucket=bucket, Key=key)
        return response['Body'].read()


    def write_png(self, bucket: str, key: str, image_bytes: bytes) -> None:
        """Write bytes to S3 as PNG file"""

        self.s3_client.put_object(Bucket=bucket, Key=key, Body=image_bytes, ContentType='image/png')


    def read_pdf(self, bucket: str, key: str) -> bytes:
        """Read PDF file from S3 and return as bytes"""

        response = self.s3_client.get_object(Bucket=bucket, Key=key)
        return response['Body'].read()


    def write_pdf(self, bucket: str, key: str, pdf_bytes: bytes) -> None:
        """Write bytes to S3 as PDF file"""

        self.s3_client.put_object(Bucket=bucket,Key=key, Body=pdf_bytes, ContentType='application/pdf')
