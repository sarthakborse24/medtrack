"""
MedTrack — DynamoDB Table Provisioner
Run once to create all required tables.

Usage:
    python create_tables.py

Uses boto3's default credential chain — no hardcoded keys.
Set AWS_REGION in your environment or .env file before running.
"""
import os
import sys
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

load_dotenv()

REGION = os.environ.get("AWS_REGION", "us-east-1")

TABLES = [
    {
        "TableName": os.environ.get("PATIENTS_TABLE", "MedTrack_Patients"),
        "KeySchema": [{"AttributeName": "PatientID", "KeyType": "HASH"}],
        "AttributeDefinitions": [{"AttributeName": "PatientID", "AttributeType": "S"}],
        "BillingMode": "PAY_PER_REQUEST",
    },
    {
        "TableName": os.environ.get("DOCTORS_TABLE", "MedTrack_Doctors"),
        "KeySchema": [{"AttributeName": "DoctorID", "KeyType": "HASH"}],
        "AttributeDefinitions": [{"AttributeName": "DoctorID", "AttributeType": "S"}],
        "BillingMode": "PAY_PER_REQUEST",
    },
    {
        "TableName": os.environ.get("APPOINTMENTS_TABLE", "MedTrack_Appointments"),
        "KeySchema": [{"AttributeName": "AppointmentID", "KeyType": "HASH"}],
        "AttributeDefinitions": [
            {"AttributeName": "AppointmentID", "AttributeType": "S"},
        ],
        "BillingMode": "PAY_PER_REQUEST",
        # NOTE: GSIs on PatientID and DoctorID should be added via the AWS
        # console or by uncommenting and configuring the block below after
        # adjusting BillingMode / throughput to match your account settings.
        #
        # "GlobalSecondaryIndexes": [
        #     {
        #         "IndexName": "PatientID-index",
        #         "KeySchema": [{"AttributeName": "PatientID", "KeyType": "HASH"}],
        #         "AttributeDefinitions": [
        #             {"AttributeName": "PatientID", "AttributeType": "S"}
        #         ],
        #         "Projection": {"ProjectionType": "ALL"},
        #     },
        #     {
        #         "IndexName": "DoctorID-index",
        #         "KeySchema": [{"AttributeName": "DoctorID", "KeyType": "HASH"}],
        #         "AttributeDefinitions": [
        #             {"AttributeName": "DoctorID", "AttributeType": "S"}
        #         ],
        #         "Projection": {"ProjectionType": "ALL"},
        #     },
        # ],
    },
    {
        "TableName": os.environ.get("DIAGNOSIS_REPORTS_TABLE", "MedTrack_DiagnosisReports"),
        "KeySchema": [{"AttributeName": "ReportID", "KeyType": "HASH"}],
        "AttributeDefinitions": [{"AttributeName": "ReportID", "AttributeType": "S"}],
        "BillingMode": "PAY_PER_REQUEST",
    },
]


def create_tables():
    dynamodb = boto3.client("dynamodb", region_name=REGION)
    created = []
    skipped = []

    for table_def in TABLES:
        table_name = table_def["TableName"]
        try:
            dynamodb.create_table(**table_def)
            print(f"  ✓ Created table: {table_name}")
            created.append(table_name)
        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceInUseException":
                print(f"  – Skipped (already exists): {table_name}")
                skipped.append(table_name)
            else:
                print(f"  ✗ Error creating {table_name}: {e}", file=sys.stderr)
                raise

    print(f"\nDone. Created: {len(created)}, Skipped: {len(skipped)}")

    if created:
        print("\nWaiting for tables to become ACTIVE...")
        dynamodb_resource = boto3.resource("dynamodb", region_name=REGION)
        for name in created:
            table = dynamodb_resource.Table(name)
            table.wait_until_exists()
            print(f"  ✓ Active: {name}")


if __name__ == "__main__":
    print(f"Creating MedTrack DynamoDB tables in region: {REGION}\n")
    create_tables()
