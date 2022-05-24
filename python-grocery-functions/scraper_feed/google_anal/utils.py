import json
from googleapiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials

KEY_FILE_LOCATION = "scraper_feed/google_anal/_SECRET_mpnmpn-779aa439f931.json"
SCOPES = ["https://www.googleapis.com/auth/analytics.readonly"]

sites = {
    "bygg-de": {"view_id": "250610345", "offer_string": "/angebote/"},
    "amp-de": {"view_id": "250230468", "offer_string": "/angebote/"},
    "beauty-de": {"view_id": "258034618", "offer_string": "/angebote/"},
    "amp-dk": {"view_id": "252921853", "offer_string": "/tilbud/"},
    "bygg-dk": {"view_id": "252899683", "offer_string": "/tilbud/"},
    "beauty-dk": {"view_id": "260140598", "offer_string": "/tilbud/"},
    "bygg-no": {"view_id": "209692000", "offer_string": "/tilbud/"},
    "beauty-no": {"view_id": "239885466", "offer_string": "/tilbud/"},
    "amp-no": {"view_id": "187893382", "offer_string": "/tilbud/"},
    "bygg-se": {"view_id": "234405434", "offer_string": "/erbjudande/"},
    "beauty-se": {"view_id": "240724194", "offer_string": "/erbjudande/"},
    "amp-se": {"view_id": "234437137", "offer_string": "/erbjudande/"},
    "bygg-uk": {"view_id": "252885276", "offer_string": "/offers/"},
    "beauty-uk": {"view_id": "252859573", "offer_string": "/offers/"},
    "amp-uk": {"view_id": "252812272", "offer_string": "/offers/"},
    "bygg-us": {"view_id": "252892165", "offer_string": "/offers/"},
    "beauty-us": {"view_id": "252892678", "offer_string": "/offers/"},
    "amp-us": {"view_id": "252904698", "offer_string": "/offers/"},
    "amp-sg": {"view_id": "259127102", "offer_string": "/offers/"},
    "amp-th": {"view_id": "260302533", "offer_string": "/offers/"},
    "amp-fr": {"view_id": "264265058", "offer_string": "/offres/"},
    "amp-nl": {"view_id": "264267478", "offer_string": "/aanbiedingen/"},
    "amp-fi": {"view_id": "258038429", "offer_string": "/tarjouksia/"},
    "amp-pl": {"view_id": "267282044", "offer_string": "/oferty/"},
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
