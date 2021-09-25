"""
Grab book offers
"""
from glom import glom
from xrpl.clients.json_rpc_client import JsonRpcClient
from xrpl.models.currencies import IssuedCurrency, XRP
from xrpl.models.requests.book_offers import BookOffers


MAINNET_BITSTAMP = "rvYAfWj5gh67oV6fW32ZzP3Aw4Eubs59B"
MAINNET_GATEHUB = "rhub8VRN55s94qWKDv6jmDy1pUykJzF3wq"


client = JsonRpcClient("https://xrplcluster.com")


EUR_bitstamp = IssuedCurrency(currency="EUR", issuer=MAINNET_BITSTAMP)
EUR_gatehub = IssuedCurrency(currency="EUR", issuer=MAINNET_GATEHUB)
JPY_bitstamp = IssuedCurrency(currency="JPY", issuer=MAINNET_BITSTAMP)
USD_bitstamp = IssuedCurrency(currency="USD", issuer=MAINNET_BITSTAMP)
USD_gatehub = IssuedCurrency(currency="USD", issuer=MAINNET_GATEHUB)

dev_sample_pairs = [
    EUR_bitstamp,
    EUR_gatehub,
    JPY_bitstamp,
    USD_bitstamp,
    USD_gatehub,
]


def get_book_offers(taker_gets, taker_pays):
    book_offers_request = BookOffers(
        taker_gets=taker_gets, taker_pays=taker_pays, limit=500
    )
    book_offers_response = client.request(book_offers_request)
    book_offers = book_offers_response.result["offers"]
    return book_offers


# bitstamp_usd__xrp_offers_request = BookOffers(
#     taker_gets=XRP(), taker_pays=USD_bitstamp, limit=500
# )
# bitstamp_usd__xrp_offers_response = client.request(bitstamp_usd__xrp_offers_request)
# bitstamp_usd__xrp_offers = bitstamp_usd__xrp_offers_response.result["offers"]
bitstamp_usd__xrp_offers = get_book_offers(XRP(), USD_bitstamp)
bitstamp_xrp__usd_offers = get_book_offers(USD_bitstamp, XRP())


# gatehub_usd__xrp_offers_request = BookOffers(
#     taker_gets=XRP(), taker_pays=USD_gatehub, limit=500
# )
# gatehub_usd__xrp_offers_response = client.request(bitstamp_usd__xrp_offers_request)
# gatehub_usd__xrp_offers = gatehub_usd__xrp_offers_response.result["offers"]
gatehub_usd__xrp_offers = get_book_offers(XRP(), USD_gatehub)
gatehub_xrp__usd_offers = get_book_offers(USD_gatehub, XRP())


glom_spec_xrp_any = {
    "TakerGets": "TakerGets",
    "TakerPays": ("TakerPays", "value"),
}

glom_spec_any_xrp = {
    "TakerPays": "TakerPays",
    "TakerGets": ("TakerGets", "value"),
}
# combined_usd_offers = glom(bitstamp_usd__xrp_offers, [glom_spec_xrp_any]) + glom(
#     gatehub_usd__xrp_offers, [glom_spec_xrp_any]
# )
combined_usd_offers = [
    offer
    for glommed in [
        glom(offers, [glom_spec_xrp_any])
        for offers in [
            bitstamp_usd__xrp_offers,
            gatehub_usd__xrp_offers,
        ]
    ]
    + [
        glom(offers, [glom_spec_any_xrp])
        for offers in [
            bitstamp_xrp__usd_offers,
            gatehub_xrp__usd_offers,
        ]
    ]
    for offer in glommed
]

combind_eur_offers = [
    offer
    for glommed in [
        glom(offers, [glom_spec_xrp_any])
        for offers in [
            get_book_offers(XRP(), EUR_bitstamp),
            get_book_offers(XRP(), EUR_gatehub),
        ]
    ]
    for offer in glommed
]
    # ] + [
    #     glom(offers, [glom_spec_any_xrp])
    #     for offers in [
    #         get_book_offers(EUR_bitstamp, 

print(len(combined_usd_offers))
