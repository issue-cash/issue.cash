import os
import pathlib

import boto3

from jinja2 import Environment, FileSystemLoader, select_autoescape


dynamodb = boto3.resource("dynamodb")

ISSUERS_TABLE_NAME = os.environ["ISSUERS_TABLE_NAME"]

issuers_table = dynamodb.Table(ISSUERS_TABLE_NAME)

# index_html = pathlib.Path("index.html").read_text()

jinja_env = Environment(
    loader=FileSystemLoader("templates"),
    autoescape=select_autoescape(),
)

index_template = jinja_env.get_template("index.html")

# Remember this is testnet, these scans include 
# the ephemeral secret seed for this round marketplaces are infinite
issuers_table_scan_resp = issuers_table.scan()
issuers = issuers_table_scan_resp["Items"]


def handler(event, context):
    print("##EVENT")
    print(event)
    print("issuers are", issuers)
    index_html = index_template.render(issuers=issuers)
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "text/html"},
        "body": index_html,
    }
