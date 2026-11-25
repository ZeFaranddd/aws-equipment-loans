import json
import os
import uuid
from datetime import datetime, timezone

import boto3

table = boto3.resource("dynamodb").Table(os.environ.get("TABLE_NAME", "equipment"))


def response(status, body):
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body, default=str),
    }


def lambda_handler(event, context):
    method = event["requestContext"]["http"]["method"]
    item_id = (event.get("pathParameters") or {}).get("id")

    try:
        # CREATE
        if method == "POST":
            data = json.loads(event.get("body") or "{}")
            if not data.get("name"):
                return response(400, {"error": "name is required"})
            item = {
                "id": str(uuid.uuid4()),
                "name": data["name"],
                "category": data.get("category", ""),
                "status": data.get("status", "available"),
                "borrower": data.get("borrower", ""),
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            table.put_item(Item=item)
            return response(201, item)

        # LIST (bonus)
        if method == "GET" and not item_id:
            return response(200, table.scan().get("Items", []))

        # READ
        if method == "GET":
            result = table.get_item(Key={"id": item_id}).get("Item")
            if not result:
                return response(404, {"error": "not found"})
            return response(200, result)

        # UPDATE
        if method == "PUT":
            data = json.loads(event.get("body") or "{}")
            if not table.get_item(Key={"id": item_id}).get("Item"):
                return response(404, {"error": "not found"})
            table.update_item(
                Key={"id": item_id},
                UpdateExpression="SET #n=:n, category=:c, #s=:s, borrower=:b",
                ExpressionAttributeNames={"#n": "name", "#s": "status"},
                ExpressionAttributeValues={
                    ":n": data.get("name", ""),
                    ":c": data.get("category", ""),
                    ":s": data.get("status", "available"),
                    ":b": data.get("borrower", ""),
                },
            )
            return response(200, table.get_item(Key={"id": item_id})["Item"])

        # DELETE
        if method == "DELETE":
            table.delete_item(Key={"id": item_id})
            return response(200, {"deleted": item_id})

        return response(405, {"error": "method not allowed"})
    except Exception as e:
        return response(500, {"error": str(e)})