# -*- coding: utf-8 -*-
import hashlib
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
UPLOAD_RECORD_FILE = "uploaded_files.txt"

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


def get_file_md5(file_path):
    """Calculate MD5 value of a file"""
    with open(file_path, "rb") as file:
        file_data = file.read()
        return hashlib.md5(file_data).hexdigest()


def get_uploaded_files():
    """Get records of uploaded files"""
    uploaded_files = {}
    if os.path.exists(UPLOAD_RECORD_FILE):
        with open(UPLOAD_RECORD_FILE, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    parts = line.strip().split(" ", 1)
                    if len(parts) == 2:
                        file_name, md5 = parts
                        uploaded_files[file_name] = md5
    return uploaded_files


def update_uploaded_files(file_name, md5):
    """Update the record of uploaded files"""
    uploaded_files = get_uploaded_files()
    uploaded_files[file_name] = md5

    with open(UPLOAD_RECORD_FILE, "w", encoding="utf-8") as f:
        for name, hash_value in uploaded_files.items():
            f.write(f"{name} {hash_value}\n")


def sync_bucket_files():
    """Sync all files from bucket to local record"""
    print("Syncing file list from bucket...")
    uploaded_files = {}

    # Paginate to get all objects
    paginator = s3_client.get_paginator("list_objects_v2")
    pages = paginator.paginate(Bucket=BUCKET_NAME)

    for page in pages:
        if "Contents" in page:
            for obj in page["Contents"]:
                file_name = obj["Key"]
                # Get object's ETag (typically MD5, with exceptions for composite objects)
                response = s3_client.head_object(Bucket=BUCKET_NAME, Key=file_name)
                md5 = response["ETag"].strip('"')
                uploaded_files[file_name] = md5

    # Update local record file
    with open(UPLOAD_RECORD_FILE, "w", encoding="utf-8") as f:
        for name, hash_value in uploaded_files.items():
            f.write(f"{name} {hash_value}\n")

    print(f"Sync completed, {len(uploaded_files)} files found")
    return uploaded_files


def upload_to_r2(file_path, uploaded_files):
    """Upload file to R2 storage"""
    try:
        file_name = file_path.name
        local_md5 = get_file_md5(file_path)

        # Check if file already uploaded with same MD5
        if file_name in uploaded_files and uploaded_files[file_name] == local_md5:
            return "skipped"

        # Upload file
        with open(file_path, "rb") as file:
            s3_client.upload_fileobj(
                Fileobj=file,
                Bucket=BUCKET_NAME,
                Key=file_name,
                ExtraArgs={"ContentType": "image/png"},
            )

        # Update local record
        update_uploaded_files(file_name, local_md5)
        return "uploaded"

    except Exception as e:
        print(f"Upload failed: {str(e)}")
        return "failed"


def main():
    # Check if initial bucket sync is needed
    if not os.path.exists(UPLOAD_RECORD_FILE):
        print("Local record file doesn't exist, performing initial bucket sync...")
        uploaded_files = sync_bucket_files()
    else:
        print(f"Loading uploaded file records from {UPLOAD_RECORD_FILE}...")
        uploaded_files = get_uploaded_files()
        print(f"Loaded {len(uploaded_files)} file records")

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
            result = upload_to_r2(file_path, uploaded_files)
            if result == "uploaded":
                progress.set_postfix_str(f"uploaded {file_path.name}")
            elif result == "skipped":
                progress.set_postfix_str(f"skipped {file_path.name}")
            else:
                progress.set_postfix_str(f"✗ {file_path.name}")

    print("\nAll uploads completed!")


if __name__ == "__main__":
    main()
