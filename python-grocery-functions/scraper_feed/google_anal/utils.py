import json
from googleapiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials
from google.analytics import data_v1beta

KEY_FILE_LOCATION = "scraper_feed/google_anal/_SECRET_mpnmpn-779aa439f931.json"
SCOPES = ["https://www.googleapis.com/auth/analytics.readonly"]

sites = {
    "bygg-de": {
        "view_id": "250610345",
        "offer_string": "/angebote/",
        "property_id": "379963269",
        "market": "de",
    },
    "amp-de": {
        "view_id": "250230468",
        "offer_string": "/angebote/",
        "market": "de",
        "property_id": "383781360",
    },
    "beauty-de": {
        "view_id": "258034618",
        "offer_string": "/angebote/",
        "market": "de",
        "property_id": "388051215",
    },
    "amp-dk": {
        "view_id": "252921853",
        "offer_string": "/tilbud/",
        "market": "dk",
        "property_id": "386170086",
    },
    "bygg-dk": {
        "view_id": "252899683",
        "offer_string": "/tilbud/",
        "market": "dk",
        "property_id": "383808265",
    },
    "beauty-dk": {
        "view_id": "260140598",
        "offer_string": "/tilbud/",
        "market": "dk",
        "property_id": "388045017",
    },
    "amp-es": {"offer_string": "/ofertas/", "market": "es", "property_id": "383683657"},
    "amp-it": {"offer_string": "/offerte/", "market": "it", "property_id": "380730750"},
    "bygg-no": {
        "view_id": "209692000",
        "offer_string": "/tilbud/",
        "market": "no",
        "property_id": "387996208",
    },
    "beauty-no": {
        "view_id": "239885466",
        "offer_string": "/tilbud/",
        "market": "no",
        "property_id": "383806805",
    },
    "amp-no": {
        "view_id": "187893382",
        "offer_string": "/tilbud/",
        "property_id": "383857545",
        "market": "no",
    },
    "supp-no": {
        "offer_string": "/tilbud/",
        "property_id": "383718592",
        "market": "no",
    },
    "bygg-se": {
        "view_id": "234405434",
        "offer_string": "/erbjudande/",
        "market": "se",
        "property_id": "383791662",
    },
    "beauty-se": {
        "view_id": "240724194",
        "offer_string": "/erbjudande/",
        "market": "se",
        "property_id": "383593315",
    },
    "amp-se": {
        "view_id": "234437137",
        "offer_string": "/erbjudande/",
        "market": "se",
        "property_id": "383784307",
    },
    "bygg-uk": {
        "view_id": "252885276",
        "offer_string": "/offers/",
        "market": "uk",
        "property_id": "388055713",
    },
    "beauty-uk": {
        "view_id": "252859573",
        "offer_string": "/offers/",
        "market": "uk",
        "property_id": "388007764",
    },
    "amp-uk": {
        "view_id": "252812272",
        "offer_string": "/offers/",
        "market": "uk",
        "property_id": "388042929",
    },
    "bygg-us": {
        "view_id": "252892165",
        "offer_string": "/offers/",
        "market": "us",
        "property_id": "388047329",
    },
    "beauty-us": {
        "view_id": "252892678",
        "offer_string": "/offers/",
        "market": "us",
        "property_id": "388052133",
    },
    "amp-us": {
        "view_id": "252904698",
        "offer_string": "/offers/",
        "market": "us",
        "property_id": "388043213",
    },
    "amp-sg": {
        "view_id": "259127102",
        "offer_string": "/offers/",
        "market": "sg",
        "property_id": "388056049",
    },
    "amp-th": {
        "view_id": "260302533",
        "offer_string": "/offers/",
        "market": "th",
        "property_id": "388052457",
    },
    "amp-fr": {
        "view_id": "264265058",
        "offer_string": "/offres/",
        "market": "fr",
        "property_id": "380727483",
    },
    "amp-nl": {
        "view_id": "264267478",
        "offer_string": "/aanbiedingen/",
        "market": "nl",
        "property_id": "383695999",
    },
    "amp-fi": {
        "view_id": "258038429",
        "offer_string": "/tarjouksia/",
        "property_id": "383698726",
        "market": "fi",
    },
    "amp-pl": {
        "view_id": "267282044",
        "offer_string": "/oferty/",
        "market": "pl",
        "property_id": "383734421",
    },
    "amp-au": {
        "view_id": "267282044",
        "offer_string": "/offers/",
        "property_id": "383689129",
        "market": "au",
    },
}


def initialize_analyticsreporting():
    """Initializes an Analytics Reporting API V4 service object.

    Returns:
      An authorized Analytics Reporting API V4 service object.
    """
    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        KEY_FILE_LOCATION, SCOPES
    )

    # Build the service object.
    analytics = build("analyticsreporting", "v4", credentials=credentials)

    return analytics


def get_analytics_data_client() -> data_v1beta.BetaAnalyticsDataClient:
    client: data_v1beta.BetaAnalyticsDataClient = (
        data_v1beta.BetaAnalyticsDataClient.from_service_account_json(KEY_FILE_LOCATION)
    )
    return client
