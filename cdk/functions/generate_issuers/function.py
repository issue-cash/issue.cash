import os
from datetime import datetime

import boto3

from xrpl.clients import JsonRpcClient
from xrpl.models.amounts import IssuedCurrencyAmount, Amount
from xrpl.models.transactions import (
    AccountSet,
    AccountSetFlag,
    # Payment,
    # TrustSet,
)
from xrpl.wallet import Wallet
from xrpl.transaction import (
    safe_sign_and_autofill_transaction,
    send_reliable_submission,
    # submit_transaction,
)

# Testnet client
testnet_client = JsonRpcClient("https://s.altnet.rippletest.net:51234")

dynamodb = boto3.resource("dynamodb")

ISSUERS_TABLE_NAME = os.environ["ISSUERS_TABLE_NAME"]

issuers_table = dynamodb.Table(ISSUERS_TABLE_NAME)


def handler(event, context):
    # return "Hello, World!"
    wallet_seed = event["seed"]
    wallet_account = event["account"]
    issuer_wallet = Wallet(seed=wallet_seed, sequence=None)

    issuer_wallet_set_tx_missing = AccountSet(
        account=issuer_wallet.classic_address,
        # TODO: this should match an average expected in production
        transfer_rate=0,
        tick_size=5,
        # tick_size=0,
        set_flag=AccountSetFlag.ASF_DEFAULT_RIPPLE,
    )
    issuer_wallet_set_tx = safe_sign_and_autofill_transaction(
        issuer_wallet_set_tx_missing, issuer_wallet, testnet_client
    )
    issuer_wallet_set_tx_resp = send_reliable_submission(
        issuer_wallet_set_tx,
        testnet_client,
    )
    # persist issuers
    # TODO the returned data is every row we persist
    # put_resp = issuers_table.put_item(
    #     Item=dict(
    #         issuer_currency="USD",
    #         seed=wallet_seed,
    #         account=wallet_account,
    #         market_epoch=datetime.utcnow().isoformat(),
    #     ),
    # )
    return {
        "issuers": {
            "USD": {"seed": wallet_seed, "acct": wallet_account},
            # TODO expand to all issuers
            "dfg": {"seed": "123", "acct": "abc123"},
        }
    }
