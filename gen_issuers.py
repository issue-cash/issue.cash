"""
Generate issuers, persist to file
"""
# import asyncio
import csv

import json
from random import sample
from rich import print
from decimal import Decimal, getcontext as decimalgetcontext

from xrpl.clients import JsonRpcClient

# from xrpl.asyncio.clients import AsyncWebsocketClient
from xrpl.ledger import get_latest_open_ledger_sequence, get_fee
from xrpl.models.amounts import IssuedCurrencyAmount, Amount
from xrpl.models.transactions import (
    AccountSet,
    AccountSetFlag,
    OfferCreate,
    OfferCreateFlag,
    Payment,
    TrustSet,
)
from xrpl.transaction import (
    safe_sign_and_submit_transaction,
    safe_sign_transaction,
    safe_sign_and_autofill_transaction,
    send_reliable_submission,
    submit_transaction,
)
from xrpl.wallet import generate_faucet_wallet, Wallet
from xrpl.utils import drops_to_xrp, xrp_to_drops


# for the faucet test looking at the url, while i'm tunneling my host
faucet_client = JsonRpcClient("https://s.altnet.rippletest.net:51234")
testnet_client = JsonRpcClient("http://localhost:5006")

ISSUER_CURRENCIES = {
    "USD",
    "EUR",
    "JPY",
}

# not a secret
dump_wallet = Wallet(seed="sEdVeCyx2k8caQuEL2otXeVAJdMRM2N", sequence=None)
# dump_wallet = Wallet(seed="sEdVmr91rBEXxkAgr4CWUVFd43SZG5G", sequence=None)


def gen_issuer(currency: str):
    """Generate an Issuer for a currency"""
    issuer_wallet = generate_faucet_wallet(faucet_client, None, True)
    return issuer_wallet


# async def issue_cash(currency, issuer_wallet):
# async with AsyncWebsocketClient("ws://localhost:6006") as client:
def issue_cash(issuer_wallet, currency, issue_to, client):
    issuer_wallet_set_tx = AccountSet(
        account=issuer_wallet.classic_address,
        # TODO: this should match an average expected in production
        transfer_rate=0,
        tick_size=5,
        # tick_size=0,
        set_flag=AccountSetFlag.ASF_DEFAULT_RIPPLE,
    )
    issuer_wallet_set_tx = safe_sign_and_autofill_transaction(
        issuer_wallet_set_tx, issuer_wallet, client
    )
    issuer_wallet_set_tx_resp = send_reliable_submission(
        issuer_wallet_set_tx,
        client,
    )
    # mint
    issued_cash_limit = IssuedCurrencyAmount(
        currency=currency,
        issuer=issuer_wallet.classic_address,
        value="1" + "0" * 9,
    )
    issued_cash = IssuedCurrencyAmount(
        currency=currency,
        issuer=issuer_wallet.classic_address,
        value="1" + "0" * 6,
    )
    dump_wallet_trustline_set_tx_missing = TrustSet(
        # account=dump_wallet.classic_address,
        account=issue_to.classic_address,
        limit_amount=issued_cash_limit,
    )
    dump_wallet_trustline_set_tx = safe_sign_and_autofill_transaction(
        transaction=dump_wallet_trustline_set_tx_missing,
        # wallet=dump_wallet,
        wallet=issue_to,
        client=client,
    )
    # dump_wallet_trustline_set_tx_resp = send_reliable_submission(dump_wallet_trustline_set_tx, client)
    dump_wallet_trustline_set_tx_resp = submit_transaction(
        dump_wallet_trustline_set_tx, client
    )

    dump_wallet_issuance_tx_missing = Payment(
        account=issuer_wallet.classic_address,
        # destination=dump_wallet.classic_address,
        destination=issue_to.classic_address,
        amount=issued_cash,
    )
    dump_wallet_issuance_tx = safe_sign_and_autofill_transaction(
        dump_wallet_issuance_tx_missing,
        wallet=issuer_wallet,
        client=client,
    )

    # dump_wallet_issuance_tx_resp = send_reliable_submission(dump_wallet_issuance_tx, client)
    dump_wallet_issuance_tx_resp = submit_transaction(dump_wallet_issuance_tx, client)


issuers = [gen_issuer(currency) for currency in ISSUER_CURRENCIES]
with open("issuers.csv", "w", newline="", encoding="utf-8") as csvfile:
    temp_account_writer = csv.DictWriter(csvfile, fieldnames=["seed", "address"])
    temp_account_writer.writeheader()
    temp_account_writer.writerows(
        [{"seed": issuer.seed, "address": issuer.classic_address} for issuer in issuers]
    )
# with open("issuers3.txt", "a") as fp:
#     fp.writelines(
#         [
#             f"seed: {issuer.seed} address: {issuer.classic_address}\n"
#             for issuer in issuers
#         ]
#     )

#
# issue cash and currency for this round
for issuer, currency in zip(issuers, ISSUER_CURRENCIES):
    issue_cash(issuer, currency, dump_wallet, testnet_client)


mapped_issuers = dict(zip(ISSUER_CURRENCIES, issuers))
print(mapped_issuers)

# use order book to make orders
with open("usd_book_offers.json", "r", encoding="utf-8") as jsonfile:
    usd_orders = json.load(jsonfile)

order_accounts: set = {order["Account"] for order in usd_orders}
print(len(order_accounts))

# slice_of_order_accounts = sample(order_accounts, 4)
slice_of_order_accounts = sample(list(order_accounts), 40)
# slice_of_order_accounts = sample(list(order_accounts), 100)
# slice_of_order_accounts = list(order_accounts)
temp_wallets = []
#

# match our tick size
# decimalgetcontext().prec = 6


def get_amount(currency, amount):
    if currency == "XRP":
        return amount


for account in slice_of_order_accounts:
    temp_wallet = generate_faucet_wallet(faucet_client, None, True)
    # issue_cash(mapped_issuers["USD"], "USD", temp_wallet, testnet_client)
    issuer_wallet = mapped_issuers["USD"]
    currency = "USD"
    issued_cash_limit = IssuedCurrencyAmount(
        currency=currency,
        issuer=issuer_wallet.classic_address,
        value="1" + "0" * 9,
    )
    issued_cash = IssuedCurrencyAmount(
        currency=currency,
        issuer=issuer_wallet.classic_address,
        value="1" + "0" * 6,
    )
    dump_wallet_trustline_set_tx_missing = TrustSet(
        # account=dump_wallet.classic_address,
        account=temp_wallet.classic_address,
        limit_amount=issued_cash_limit,
    )
    dump_wallet_trustline_set_tx = safe_sign_and_autofill_transaction(
        transaction=dump_wallet_trustline_set_tx_missing,
        # wallet=dump_wallet,
        wallet=temp_wallet,
        client=testnet_client,
    )
    # dump_wallet_trustline_set_tx_resp = send_reliable_submission(dump_wallet_trustline_set_tx, testnet_client)
    dump_wallet_trustline_set_tx_resp = submit_transaction(
        dump_wallet_trustline_set_tx, testnet_client
    )

    dump_wallet_issuance_tx_missing = Payment(
        account=issuer_wallet.classic_address,
        # destination=dump_wallet.classic_address,
        destination=temp_wallet.classic_address,
        amount=issued_cash,
    )
    dump_wallet_issuance_tx = safe_sign_and_autofill_transaction(
        dump_wallet_issuance_tx_missing,
        wallet=issuer_wallet,
        client=testnet_client,
    )

    dump_wallet_issuance_tx_resp = send_reliable_submission(
        dump_wallet_issuance_tx, testnet_client
    )
    # dump_wallet_issuance_tx_resp = submit_transaction(
    #     dump_wallet_issuance_tx, testnet_client
    # )
    for my_order in (
        my_orders := filter(lambda order: order["Account"] == account, usd_orders)
    ):

        # we know this datas taker_gets are XRP
        # this_order_taker_gets_currency = my_order["TakerGets"]
        this_order_taker_gets_raw = my_order["TakerGetsAmount"]
        represented_xrp = drops_to_xrp(this_order_taker_gets_raw)
        # we need to keep this under our faucet value for now of 1000 xrp
        # TODO, fail the offer?
        # this_order_taker_gets: str = xrp_to_drops(represented_xrp % 990)
        # this_order_taker_gets: str = xrp_to_drops(represented_xrp % 990)
        this_order_taker_gets: str = xrp_to_drops(represented_xrp)
        
        this_order_taker_gets = get_amount(my_order["TakerGets"], my_order["TakerGetsAmount"])

        # normalization_factor = Decimal(this_order_taker_gets) / Decimal(xrp_to_drops(represented_xrp))
        normalization_factor = 1

        this_order_issuer = mapped_issuers[
            my_order["TakerPaysCurrency"]
        ].classic_address
        this_order_taker_pays_value_raw: Decimal = Decimal(my_order["TakerPaysAmount"]) * normalization_factor
        # this_order_taker_pays_value = this_order_taker_pays_value_raw / (
        #     represented_xrp % 990
        # )
        # normalized_value = int(this_order_taker_pays_value_raw) or 1
        normalized_value = int(this_order_taker_pays_value_raw) or Decimal("0.01")
        this_order_taker_pays = IssuedCurrencyAmount(
            currency=my_order["TakerPaysCurrency"],
            issuer=this_order_issuer,
            # value=f"{int(this_order_taker_pays_value)}",
            value=f"{normalized_value}",
        )

        # create_my_offer_tx = OfferCreate(
        create_my_offer_tx_missing = OfferCreate(
            account=temp_wallet.classic_address,
            taker_gets=this_order_taker_gets,
            taker_pays=this_order_taker_pays,
            # taker_gets=this_order_taker_pays,
            # taker_pays=this_order_taker_gets,
            flags=OfferCreateFlag.TF_PASSIVE,
            fee="10",
            # sequence=get_latest_open_ledger_sequence(testnet_client) + 10,
        )
        print("gets", this_order_taker_gets, "pays", this_order_taker_pays)
        create_my_offer_tx = safe_sign_and_autofill_transaction(
            create_my_offer_tx_missing,
            wallet=temp_wallet,
            client=testnet_client,
            check_fee=False,
        )

        # create_my_offer_signed_and_sent = safe_sign_and_submit_transaction(
        #     create_my_offer_tx_missing, temp_wallet, testnet_client, True, True
        # )

        try:
            create_my_offer_resp = send_reliable_submission(
                create_my_offer_tx, testnet_client
            )
            # crazy??
            # create_my_offer_tx_missing = OfferCreate(
            #     account=temp_wallet.classic_address,
            #     taker_gets=this_order_taker_pays,
            #     taker_pays=this_order_taker_gets,
            #     flags=OfferCreateFlag.TF_PASSIVE,
            #     fee="10",
            #     # sequence=get_latest_open_ledger_sequence(testnet_client) + 10,
            # )
            # print("gets other side", this_order_taker_gets, "pays other side", this_order_taker_pays)
            # create_my_offer_tx = safe_sign_and_autofill_transaction(
            #     create_my_offer_tx_missing,
            #     wallet=temp_wallet,
            #     client=testnet_client,
            #     check_fee=False,
            # )
            #
            # # create_my_offer_signed_and_sent = safe_sign_and_submit_transaction(
            # #     create_my_offer_tx_missing, temp_wallet, testnet_client, True, True
            # # )
            #
            # create_my_offer_resp = send_reliable_submission(
            #     create_my_offer_tx, testnet_client
            # )
            # # create_my_offer_resp = submit_transaction(
            # #     create_my_offer_tx, testnet_client
            # # )
        except Exception:
            continue

    temp_wallets.append(
        {"seed": temp_wallet.seed, "account": temp_wallet.classic_address}
    )
