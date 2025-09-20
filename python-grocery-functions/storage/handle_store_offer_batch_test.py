import json
from pathlib import Path
from datetime import datetime, timedelta

from storage.postgres.scraper_feed import handle_store_offer_batch
from util.logging import configure_lambda_logging
from util.mappings import get_offer_context_from_site_collection

configure_lambda_logging()


def test_save_offers_with_postgres():
    scrape_time = datetime.fromisoformat("2024-10-03T00:00:00+00:00")

    with open(Path(__file__).parent / "offers_for_save_kolonial.json", "r") as f:
        kolonial_offers = list(
            {
                **x,
                "context": get_offer_context_from_site_collection(x["siteCollection"]),
                "validFrom": scrape_time,
                "validThrough": scrape_time + timedelta(days=7),
            }
            for x in json.load(f)
        )
    with open(Path(__file__).parent / "offers_for_save_meny.json", "r") as f:
        meny_offers = list(
            {
                **x,
                "context": get_offer_context_from_site_collection(x["siteCollection"]),
                "validFrom": scrape_time,
                "validThrough": scrape_time + timedelta(days=7),
            }
            for x in json.load(f)
        )

    # Save offers to postgres
    # handle_store_offer_batch(
    #    offers=kolonial_offers, scrape_time=scrape_time, context="amp-no"
    # )
    # handle_store_offer_batch(
    #    offers=meny_offers, scrape_time=scrape_time, context="amp-no"
    # )
    handle_store_offer_batch(
        offers=[
            {
                "price": 870.0,
                "priceCurrency": "SEK",
                "sku": "51871",
                "brand": "/Aftershave/Yves-Saint-Laurent/",
                "title": "Yves Saint Laurent Y Eau de Toilette 60ml Sprej",
                "url": "https://www.parfym-klick.se/Yves-Saint-Laurent-Y-Eau-de-Toilette-60ml-Sprej-s51871/",
                "image": "https://299df094394db9cc1de4-60c51f90a91f2305b52a889e5c1d7548.ssl.cf3.rackcdn.com/110746_xl_7.jpg",
                "description": "Yves Saint Laurent Y Eau de Toilette 60ml Sprej Y for Men av Yves Saint Laurent är en träig och aromatisk doft för män. Sammansättningen av Eau de Toilette börjar med rena noter av vita aldehyder, ingefära och bergamott som utvecklas med geranium, violetta blad och salvia i hjärtat med stöd av en maskulär bas av gran balsam, rökelse, ambergris, mysk och cederträ. Eau de Parfum delar dessa noter berikade med äpple i öppningen, enbär i hjärtat och olibanum i basen. Båda versionerna finns i en minimalistisk linjär flaska med en metallaccent som bara verkar ha märkesnamnet när du ser framsidan av flaskan, men om du vänder det visar det sig vara basen i bokstaven Y. Y skapades för att ge den generation som föddes på 80- och 90-talet en säker och mångsidig doft till skillnad från någon annan. EDT-versionen av Y for Men lanserades 2017 följt av en EDP 2018.",
                "availability": "http://schema.org/InStock",
                "itemCondition": "http://schema.org/NewCondition",
                "categories": [
                    "Parfym Klick",
                    "Dofter",
                    "För Honom",
                    "Yves Saint Laurent",
                    "Y",
                ],
                "canonical_url": "https://www.parfym-klick.se/Yves-Saint-Laurent-Y-Eau-de-Toilette-60ml-Sprej-s51871/",
                "provenance": "parfyme_klikk_se_spider",
                "url_fingerprint": "ec66ee66d93af84db49cdee0f95ee33bc89053e3",
                "provenanceId": "51871",
            }
        ],
        scrape_time=scrape_time,
        context="beauty-se",
    )


if __name__ == "__main__":
    test_save_offers_with_postgres()
