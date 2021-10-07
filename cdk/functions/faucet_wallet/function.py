import time
import random
from xrpl.clients import JsonRpcClient
from xrpl.wallet import generate_faucet_wallet


faucet_client = JsonRpcClient("https://s.altnet.rippletest.net:51234")

def handler(event, context):
    temp_wallet = None
    while temp_wallet is None:
        try:
            temp_wallet = generate_faucet_wallet(faucet_client, None)
        except Exception:
            time.sleep(10 * random.random() + 1)
    return {
        "seed": temp_wallet.seed,
        "account": temp_wallet.classic_address,
    }
