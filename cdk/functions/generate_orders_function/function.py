import time
import random
from decimal import Decimal

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
    Memo,
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

testnet_client = JsonRpcClient("https://s.altnet.rippletest.net:51234")


def get_amount(currency, amount, this_order_issuer):
    if currency == "XRP":
        return amount
    else:
        # this_order_issuer = mapped_issuers[currency].classic_address
        # raw: Decimal = Decimal(amount) * normalization_factor
        raw: Decimal = Decimal(amount)
        # this_order_taker_pays_value = this_order_taker_pays_value_raw / (
        #     represented_xrp % 990
        # )
        # normalized_value = int(this_order_taker_pays_value_raw) or 1
        # normalized_value = raw or Decimal("0.01")
        return IssuedCurrencyAmount(
            currency=currency,
            issuer=this_order_issuer,
            # value=f"{int(this_order_taker_pays_value)}",
            # value=f"{normalized_value}",
            value=f"{raw}",
        )


def handler(event, context):
    count = 0
    currency = event["issuer"]["code"]
    issuer_wallet = Wallet(seed=event["issuer"]["seed"], sequence=None)
    temp_wallet = Wallet(seed=event["wallet"]["seed"], sequence=None)
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
    temp_wallet_trustline_set_tx_missing = TrustSet(
        # account=temp_wallet.classic_address,
        account=temp_wallet.classic_address,
        limit_amount=issued_cash_limit,
    )
    temp_wallet_trustline_set_tx = safe_sign_and_autofill_transaction(
        transaction=temp_wallet_trustline_set_tx_missing,
        # wallet=temp_wallet,
        wallet=temp_wallet,
        client=testnet_client,
    )
    # temp_wallet_trustline_set_tx_resp = send_reliable_submission(temp_wallet_trustline_set_tx, testnet_client)
    temp_wallet_trustline_set_tx_resp = submit_transaction(
        temp_wallet_trustline_set_tx, testnet_client
    )

    satirical_branding = Memo(
        memo_data=(
            b"Need cash now (on the testnet)?"
            b" Get cash now (on the testnet)!"
            b" go to: https://issue.cash"
        ).hex()
    )

    while count < 5:
        try:
            temp_wallet_issuance_tx_missing = Payment(
                account=issuer_wallet.classic_address,
                # destination=temp_wallet.classic_address,
                destination=temp_wallet.classic_address,
                amount=issued_cash,
                memos=[satirical_branding],
            )
            temp_wallet_issuance_tx = safe_sign_and_autofill_transaction(
                temp_wallet_issuance_tx_missing,
                wallet=issuer_wallet,
                client=testnet_client,
            )

            temp_wallet_issuance_tx_resp = send_reliable_submission(
                temp_wallet_issuance_tx, testnet_client
            )
            break
        except Exception:
            count -= 1
            time.sleep(10 * random.random() + 1.3)

    this_order_issuer = Wallet(
        seed=event["issuer"]["seed"], sequence=None
    ).classic_address

    for offer in event["offers"]:
        this_offer_taker_gets = get_amount(offer["tg"], offer["tgv"], this_order_issuer)
        this_offer_taker_pays = get_amount(offer["tp"], offer["tpv"], this_order_issuer)
        create_my_offer_tx_missing = OfferCreate(
            account=temp_wallet.classic_address,
            taker_gets=this_offer_taker_gets,
            taker_pays=this_offer_taker_pays,
            # taker_gets=this_offer_taker_pays,
            # taker_pays=this_offer_taker_gets,
            flags=OfferCreateFlag.TF_PASSIVE,
            fee="10",
            # sequence=get_latest_open_ledger_sequence(testnet_client) + 10,
            memos=[
                Memo(memo_data=b"Offer created by issue.cash".hex()),
                satirical_branding,
            ],
        )
        create_my_offer_tx = safe_sign_and_autofill_transaction(
            create_my_offer_tx_missing,
            wallet=temp_wallet,
            client=testnet_client,
            check_fee=False,
        )
        try:
            # we need to bail before trying another offer if we have less than
            # 6 seconds
            # at a 15minute timeout; we created some offers
            if context.get_remaining_time_in_millis() < 6000:
                return
            create_my_offer_resp = send_reliable_submission(
                create_my_offer_tx, testnet_client
            )
        except Exception:
            # go onto the next offer /shrug
            continue
