"""
persist_issuers

Persist the issuers from the statemachine that had just finished issuing. This
frees up issuer limits until the market is ready.

While the frontend continues to use any previous issuers.
"""
import os

from datetime import datetime

import boto3

# from xrpl.wallet import Wallet


dynamodb = boto3.resource("dynamodb")

ISSUERS_TABLE_NAME = os.environ["ISSUERS_TABLE_NAME"]

issuers_table = dynamodb.Table(ISSUERS_TABLE_NAME)


def handler(event, context):
    print("Got event", event)

    issuers = event["issuers"]

    # persist issuers
    # TODO the returned data is every row we persist
    # just usd rn
    # currency = "USD"
    for currency, meta in issuers.items():
        wallet_seed = meta["seed"]
        wallet_account = meta["acct"]
        put_resp = issuers_table.put_item(
            Item=dict(
                issuer_currency=currency,
                seed=wallet_seed,
                account=wallet_account,
                market_epoch=datetime.utcnow().isoformat(),
            ),
        )

    return event
