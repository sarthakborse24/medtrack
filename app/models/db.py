"""
DynamoDB helper — shared boto3 resource and table accessors.
Uses boto3's default credential chain (env vars / IAM role — never hardcoded keys).
"""
import boto3
from flask import current_app


def get_dynamodb():
    """Return a boto3 DynamoDB resource using the app's configured region."""
    return boto3.resource("dynamodb", region_name=current_app.config["AWS_REGION"])


def get_table(table_name_key: str):
    """Return a DynamoDB Table object given a config key for the table name."""
    db = get_dynamodb()
    table_name = current_app.config[table_name_key]
    return db.Table(table_name)
