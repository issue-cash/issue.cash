import time
import random
from xrpl.clients import JsonRpcClient
from xrpl.wallet import generate_faucet_wallet


faucet_client = JsonRpcClient("https://s.altnet.rippletest.net:51234")

def handler(event, context):
    count = 5
    while count > 0:
        try:
            temp_wallet = generate_faucet_wallet(faucet_client, None)
            break
        except Exception:
            count -= 1
            time.sleep(10 * random.random() + 1)

    # return f"Guess that worked!, seed: {temp_wallet.seed}, account: {temp_wallet.classic_address}"
    return {
        "seed": temp_wallet.seed,
        "account": temp_wallet.classic_address,
    }
