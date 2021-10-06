import csv
from xrpl.clients import JsonRpcClient
from xrpl.models.amounts import IssuedCurrencyAmount
from xrpl.models.transactions import Payment
from xrpl.transaction import (
    safe_sign_and_autofill_transaction,
    send_reliable_submission,
    submit_transaction,
)
from xrpl.wallet import Wallet, generate_faucet_wallet
from xrpl.utils import xrp_to_drops


faucet_client = JsonRpcClient("https://s.altnet.rippletest.net:51234")
testnet_client = JsonRpcClient("http://localhost:5006")

# not a secret
DUMP_ACCOUNT = Wallet(seed="sEdVeCyx2k8caQuEL2otXeVAJdMRM2N", sequence=None)


# 1000 xrp per faucet, create; send go onto the next

# accumulate 10000 xrp
accumulate_amount = 10_000
temp_wallets = []
#
while accumulate_amount >= 0:
    temp_wallet = generate_faucet_wallet(faucet_client, None, True)

    ACCUM_AMOUNT = 990
    send_faucet_xrp_for_accumulation_tx_missing = Payment(
        account=temp_wallet.classic_address,
        destination=DUMP_ACCOUNT.classic_address,
        amount=xrp_to_drops(ACCUM_AMOUNT),
    )
    send_faucet_xrp_for_accumulation_tx = safe_sign_and_autofill_transaction(
        send_faucet_xrp_for_accumulation_tx_missing,
        wallet=temp_wallet,
        client=testnet_client,
    )
    send_faucet_xrp_for_accumulation_resp = send_reliable_submission(
        send_faucet_xrp_for_accumulation_tx, testnet_client
    )
    accumulate_amount -= ACCUM_AMOUNT
    temp_wallets.append(
        {"seed": temp_wallet.seed, "account": temp_wallet.classic_address}
    )


# csv.register_dialect("accounts", delimiter=",", quoting=csv.QUOTE_NONE)
with open("temp_accounts.csv", "w", newline="", encoding="utf-8") as csvfile:
    temp_account_writer = csv.DictWriter(csvfile, fieldnames=["seed", "account"])
    temp_account_writer.writeheader()
    temp_account_writer.writerows(temp_wallets)
