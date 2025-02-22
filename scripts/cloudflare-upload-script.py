# -*- coding: utf-8 -*-
import os
from pathlib import Path

import boto3
from botocore.config import Config
from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv()

ACCESS_KEY_ID = os.getenv("S2_ACCESS_KEY_ID")
ACCESS_KEY_SECRET = os.getenv("S2_KEY_SECRET")
ENDPOINT = os.getenv("S2_ENDPOINTS")
BUCKET_NAME = os.getenv("S2_BUCKET_NAME")

if not all([ACCESS_KEY_ID, ACCESS_KEY_SECRET, ENDPOINT, BUCKET_NAME]):
    raise ValueError("Missing required environment variables")

s3_client = boto3.client(
    "s3",
    endpoint_url=ENDPOINT,
    aws_access_key_id=ACCESS_KEY_ID,
    aws_secret_access_key=ACCESS_KEY_SECRET,
    config=Config(signature_version="s3v4"),
    region_name="auto",
)


def check_file_exists(file_path):
    try:
        file_name = file_path.name
        with open(file_path, "rb") as file:
            file_data = file.read()
            import hashlib

            local_md5 = hashlib.md5(file_data).hexdigest()

        try:
            response = s3_client.head_object(Bucket=BUCKET_NAME, Key=file_name)
            remote_etag = response["ETag"].strip('"')
            return local_md5 == remote_etag
        except:
            return False

    except Exception as e:
        print(f"Check failed: {str(e)}")
        return False


def upload_to_r2(file_path):
    if check_file_exists(file_path):
        return "skipped"

    try:
        file_name = file_path.name
        with open(file_path, "rb") as file:
            s3_client.upload_fileobj(
                Fileobj=file,
                Bucket=BUCKET_NAME,
                Key=file_name,
                ExtraArgs={"ContentType": "image/png"},
            )
        return "uploaded"

    except Exception as e:
        print(f"Upload failed: {str(e)}")
        return "failed"


def main():
    image_dir = Path("resources/images")

    if not image_dir.exists():
        print(f"Directory does not exist: {image_dir}")
        return

    png_files = list(image_dir.glob("*.png"))
    if not png_files:
        print("No PNG files found in directory")
        return

    print(f"Found {len(png_files)} PNG files")

    with tqdm(png_files, desc="Uploading files") as progress:
        for file_path in progress:
            result = upload_to_r2(file_path)
            if result == "uploaded":
                progress.set_postfix_str(f"uploaded {file_path.name}")
            elif result == "skipped":
                progress.set_postfix_str(f"skipped {file_path.name}")
            else:
                progress.set_postfix_str(f"✗ {file_path.name}")

    print("\nAll uploads completed!")


if __name__ == "__main__":
    main()
