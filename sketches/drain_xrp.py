"""
Dump a bunch of xrp testnet accounts back into somwhere useful
"""
import sys

from xrpl.clients import JsonRpcClient
from xrpl.models.amounts import IssuedCurrencyAmount
from xrpl.models.transactions import Payment
from xrpl.transaction import (
    safe_sign_and_autofill_transaction,
    send_reliable_submission,
    submit_transaction,
)
from xrpl.wallet import Wallet



testnet_client = JsonRpcClient("http://localhost:5006")

# not a secret 
# DUMP_ACCOUNT = Wallet(seed="sEdVeCyx2k8caQuEL2otXeVAJdMRM2N", sequence=None)
WALLET_SEED = sys.argv[-1]
DUMP_ACCOUNT = Wallet(seed=WALLET_SEED, sequence=None)
