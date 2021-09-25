"""
Grab book offers
"""
from glom import glom, Coalesce, SKIP
from rich import print
from xrpl.clients.json_rpc_client import JsonRpcClient
from xrpl.models.currencies import IssuedCurrency, XRP
from xrpl.models.requests.book_offers import BookOffers


MAINNET_BITSTAMP = "rvYAfWj5gh67oV6fW32ZzP3Aw4Eubs59B"
MAINNET_GATEHUB = "rhub8VRN55s94qWKDv6jmDy1pUykJzF3wq"


# client = JsonRpcClient("https://xrplcluster.com")
client = JsonRpcClient("http://localhost:5005")


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

gatehub_eur_bitstamp_eur_offers = get_book_offers(EUR_gatehub, EUR_bitstamp)

bitstamp_usd_gatehub_eur_offers = get_book_offers(USD_bitstamp, EUR_gatehub)
bitstamp_usd_eur_offers = get_book_offers(USD_bitstamp, EUR_bitstamp)
gatehub_usd_eur_offers = get_book_offers(USD_gatehub, EUR_gatehub)
bitstamp_usd_bitstamp_jpy_offers = get_book_offers(USD_bitstamp, JPY_bitstamp)
gatehub_usd_bitstamp_jpy_offers = get_book_offers(USD_gatehub, JPY_bitstamp)

# 'any' refers to 'any issued currency'; xrp is the native asset.
glom_spec_xrp_any = {
    "TakerGets": "TakerGets",
    "TakerPays": ("TakerPays", "value"),
}

glom_spec_any_xrp = {
    "TakerPays": "TakerPays",
    "TakerGets": ("TakerGets", "value"),
}

glom_spec_any_any = {
    "TakerGets": ("TakerGets", "value"),
    "TakerPays": ("TakerPays", "value"),
}

glom_spec_account_only = {
    "Account": "Account"
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
        glom(offers, [Coalesce(glom_spec_any_any, SKIP)])
        for offers in [
            bitstamp_usd_gatehub_eur_offers,
            bitstamp_usd_eur_offers,
            gatehub_usd_eur_offers,
            bitstamp_usd_bitstamp_jpy_offers,
            gatehub_usd_bitstamp_jpy_offers,
        ]
    ]
    for offer in glommed
]

all_accounts = [
    account
    for glommed in [
        # glom all our offers and create chains of lists
        glom(offers, [glom_spec_account_only])
        for offers in [
            bitstamp_usd__xrp_offers,
            gatehub_usd__xrp_offers,
            bitstamp_usd_gatehub_eur_offers,
            bitstamp_usd_eur_offers,
            gatehub_usd_eur_offers,
            bitstamp_usd_bitstamp_jpy_offers,
            gatehub_usd_bitstamp_jpy_offers,
        ]
    ]
    # unpack each chain, which is each offer
    for offer in glommed
    # take only the values, which is just our account
    for account in offer.values()
]

# combind_eur_offers = [
#     offer
#     for glommed in [
#         glom(offers, [glom_spec_xrp_any])
#         for offers in [
#             get_book_offers(XRP(), EUR_bitstamp),
#             get_book_offers(XRP(), EUR_gatehub),
#         ]
#     ]
#     for offer in glommed
# ]


print(gatehub_usd_eur_offers[5:8])
print(len(combined_usd_offers))
print(combined_usd_offers[5:8])
print(len(all_accounts))
print(all_accounts[5:8])
print(len(set(all_accounts)), "unique offer creators")
