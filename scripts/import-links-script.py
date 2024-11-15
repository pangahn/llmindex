# -*- coding: utf-8 -*-
import json
import os
from datetime import date
from pathlib import Path
from typing import List

import lark_oapi as lark
import pandas as pd
from dotenv import load_dotenv
from lark_oapi.api.bitable.v1 import (
    SearchAppTableRecordRequest,
    SearchAppTableRecordRequestBody,
    SearchAppTableRecordResponse,
)

load_dotenv()

PROJECT_PATH = Path(__file__).resolve().parent.parent
CURRENT_DATE = date.today().strftime("%Y-%m-%d")
FEISHU_APP_ID = os.getenv("FEISHU_APP_ID")
FEISHU_APP_SECRET = os.getenv("FEISHU_APP_SECRET")
BITABLE_ID = os.getenv("BITABLE_ID")
LARK_CLIENT = lark.Client.builder().app_id(FEISHU_APP_ID).app_secret(FEISHU_APP_SECRET).log_level(lark.LogLevel.INFO).build()


def get_bitable_records(table_id, view_id):
    request: SearchAppTableRecordRequest = (
        SearchAppTableRecordRequest.builder()
        .app_token(BITABLE_ID)
        .table_id(table_id)
        .page_size(100)
        .request_body(SearchAppTableRecordRequestBody.builder().view_id(view_id).build())
        .build()
    )

    response: SearchAppTableRecordResponse = LARK_CLIENT.bitable.v1.app_table_record.search(request)

    if not response.success():
        lark.logger.error(f"bitable search failed, code: {response.code}, msg: {response.msg}, log_id: {response.get_log_id()}")
        lark.logger.error(f"resp: \n{json.dumps(json.loads(response.raw.content), indent=4, ensure_ascii=False)}")
        return

    data = json.loads(lark.JSON.marshal(response.data, indent=4))
    return data


def bitable_records_to_dataframe(bitable_data: dict):
    data = []

    item_list: List[dict] = bitable_data["items"]
    for item in item_list:
        item_data = {}
        for field_name, field_data in item["fields"].items():
            if isinstance(field_data, str):
                item_data[field_name] = field_data
            elif isinstance(field_data, list) and isinstance(field_data[0], dict):
                item_data[field_name] = field_data[0]["text"]
            elif isinstance(field_data, list) and isinstance(field_data[0], str):
                item_data[field_name] = field_data
            elif isinstance(field_data, dict) and "link" in field_data:
                item_data[field_name] = field_data["link"]
            else:
                print(field_data)
                raise ValueError(f"Error: Unknown field data type, {type(field_data)}")
        data.append(item_data)

    return pd.DataFrame(data)


def main():
    CATEGORY_TABLE_ID = os.getenv("CATEGORY_TABLE_ID")
    CATEGORY_VIEW_ID = os.getenv("CATEGORY_VIEW_ID")
    category_bitable_data = get_bitable_records(CATEGORY_TABLE_ID, CATEGORY_VIEW_ID)
    category_df = bitable_records_to_dataframe(category_bitable_data)
    category_df = category_df[category_df["status"] == "active"]

    ITEM_TABLE_ID = os.getenv("ITEM_TABLE_ID")
    ITEM_VIEW_ID = os.getenv("ITEM_VIEW_ID")
    item_bitable_data = get_bitable_records(ITEM_TABLE_ID, ITEM_VIEW_ID)
    item_df = bitable_records_to_dataframe(item_bitable_data)
    item_df = item_df[item_df["status"] == "active"].fillna("")

    link_data = {
        "version": "1.0",
        "lastUpdated": CURRENT_DATE,
        "categories": {},
    }

    for _, category in category_df.iterrows():
        category_id = category["category_id"]
        item_data = []
        _item_df = item_df[item_df["category_id"] == category_id]
        for _, row in _item_df.iterrows():
            item_id = row["item_id"]
            icon = f"images/{item_id.split('-')[0]}.png"
            item_data.append(
                {
                    "id": item_id,
                    "name": row["name"],
                    "company": row["company"],
                    "url": row["url"],
                    "tranco": row["tranco"],
                    "icon": icon,
                    "features": row["features"],
                    "status": row["status"],
                }
            )

        category_data = {
            "name": category["name"],
            "description": category["description"],
            "status": category["status"],
            "items": item_data,
        }
        link_data["categories"][category_id] = category_data

    links_filename = PROJECT_PATH / "public/data/links.json"
    if not links_filename.parent.exists():
        links_filename.parent.mkdir()
    with open(links_filename, "w", encoding="utf-8") as json_file:
        json.dump(link_data, json_file, ensure_ascii=False, indent=4)
        print("Successfully retrieved site list data")


if __name__ == "__main__":
    main()
