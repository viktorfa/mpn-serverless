import json
from pathlib import Path
import pydash
from typing import Union

from amp_types.amp_product import HandleConfig, MpnOffer

categories = {}

with open(Path(Path(__file__).parent, "category-hierarchy.json")) as category_file:
    categories = json.load(category_file)
with open(Path(Path(__file__).parent, "category-extra.json")) as extra_category_file:
    extra_categories = json.load(extra_category_file)

categories = {**extra_categories, **categories}

category_mappings = {
    "kolonial": {
        # MATHALL
        "Kjøttdisken": categories["kjott_0"],
        "Fiskedisken": categories["fisk_0"],
        "Brød og bakevarer": categories["bakeri_0"],
        "Ostedisken": categories["ost_0"],
        "Meieri og egg": categories["meieri-egg_0"],
        "Drikke": categories["drikke_0"],
        "Pålegg og spekemat": categories["palegg-frokost_0"],  # No good match
        "Middagstilbehør, pasta, pizza og saus": categories["middag_0"],
        "Mel og gryn": categories["mel-og-gryn_1"],
        "Iskrem, søtsaker og snacks": categories["dessert_0"],
        # FRUKT OG GRØNT
        "Epler og pærer": categories["epler-prer"],
        "Sitrusfrukter": categories["sitrusfrukt_2"],
        "Sitrusfrukter": categories["bananer_2"],
        "Meloner": categories["melon_2"],
        "Eksotiske frukter": categories["eksotiske-frukter"],
        "Druer, kiwi og steinfrukt": categories["druer-kiwi-steinfrukt"],
        "Fruktkurv": categories["fruktkurv_1"],
        "Bær": categories["br_1"],
        "Hel salat og kål": categories["salater_2"],
        "Ferdigkuttet salat og kål": categories["salater_2"],
        "Tomater": categories["tomater_2"],
        "Avokado": categories["avocado_2"],
        "Agurk": categories["agurk_2"],
        "Paprika og chili": categories["paprika-chili"],
        "Løk og hvitløk": categories["lok_2"],
        "Sopp": categories["sopp_2"],
        "Gulrøtter, selleri og rotfrukter": categories["gulrotter-selleri-rotfrukter"],
        "Poteter": categories["poteter_2"],
        "Squash og aubergine": categories["squash-aubergine"],
        "Erter, asparges og bønner": categories["erter-asparges-bonner"],
        "Mais": categories["mais_2"],
        "Urter og spirer": categories["krydderurter_1"],
        "Frø, nøtter og tørket frukt": categories[
            "torket-frukt-og-notter_1"
        ],  # TODO Hmm
        "Hermetisert frukt og grønt": categories["hermetisk-gront_1"],
        "Fryst frukt": categories["frukt-og-br-frosne_2"],
        "Fryste grønnsaker": categories["gronnsaker-frosne_2"],
        "Pommes frites": categories["pommes-frites_2"],
        # BAKERI OG BRØD
        "Brød": categories["brod_1"],
        "Rundstykker og baguetter": categories["rundstykker-og-smabrod_1"],
        "Småbakst": categories["boller-og-smakaker_1"],
        "Brød-fryst": categories[
            "boller-og-smakaker_1"
        ],  # TODO Create category for frozen bakery??
        "Pitabrød": categories["pitabrod_1"],
        "Pita og naan": categories["pita-naan"],
        "Flatbrød": categories["flatbrod_2"],
        "Kjeks til ost": categories["smorbrodkjeks_2"],
        "Knekkebrød": categories["knekkebrod_1"],
        "Pølse- og hamburgerbrød": categories["polse-hamburgerbrod"],
        "Deiger og bunner": categories["deiger-og-rorer_1"],
        "Ferdig påsmurt": categories["ferdigmaltid_2"],
        # FROKOSTBLANDINGER OG MÜSLI
        "Frokostblandinger": categories["frokostblanding_2"],
        "Havregryn": categories["havregryn_2"],
        "Müsli og granola": categories["granola_2"],
        # MEIERI OST OG EGG
        "Melk": categories["helmelk_2"],
        "Lettmelk": categories["lettmelk_2"],
        "Skummet melk": categories["skummet-melk_2"],
        "Melk med smak": categories["melk-med-smak"],
        "Plantebasert drikke": categories["plantebasert-drikke_1"],
        "Smør og margarin": categories["smor-og-margarin_1"],
        "Egg": categories["egg_1"],
        "Fløte og rømmeprodukter": categories["flote-rommeprodukter"],
        "Små beger": categories["yoghurt_2"],
        "Store beger": categories["yoghurt_1"],  # TODO Need own subcat??
        "Barneyoghurt": categories["yoghurt_2"],
        "Yoghurt mellommåltid": categories["yoghurt_2"],
        "Gulost": categories["gulost_2"],
        "Revet ost": categories["revet-ost_1"],
        "Brunost": categories["brunost_1"],
        "Smøreost og prim": categories["smoreoster_1"],
        "Fastost": categories["parmesan-og-smaksrike-fastoster_1"],
        "Blåmuggost": categories["blamuggost_1"],
        "Hvitmuggost": categories["hvitmuggost_1"],
        "Kittmodnet ost": categories["kittmodnetost_1"],
        "Krem- og ferskost": categories["kremost_2"],
        "Chevre": categories["chevre_1"],
        # KJØTT OG KYLLING
        "Storfe og kalv": categories["storfekjott_1"],
        "Svin": categories["svinekjott_1"],
        "Kylling, kalkun og and": categories["kylling-og-fjrkre_0"],
        "Lam og vilt": categories["lam-vilt"],
        "Bacon og smårettskinke": categories["bacon-smarettskinke"],
        "Kjøttdeig og karbonadedeig": categories["kjottdeig-og-farse_1"],
        "Hamburgere": categories["hamburger_1"],
        "Kjøttboller og karbonader": categories["kjottboller-karbonader"],
        "Pølser": categories["polser_1"],
        # FISK OG SJØMAT
        "Fersk fisk": categories["fisk_1"],
        "Skalldyr": categories["skalldyr_1"],
        "Røkt og gravet fisk": categories["rokt-gravet-fisk"],
        "Fiskekaker og fiskepudding": categories["fiskekaker-fiskepudding"],
        "Hermetisert sjømat": categories["hermetisk-fisk-og-sjomat_2"],
        "Fiskefilet": categories["fisk_1"],  # TODO Frozen, need subcat?
        "Fiskegrateng": categories["fiskegrateng_2"],
        "Innbakt og panert fisk": categories["innbakt-panert-fisk"],
        # FROKOST
        "Fiskepålegg og reker i lake": categories[
            "fiskepalegg_1"
        ],  # TODO Need own subcat ??
        "Kjøttpålegg": categories["kjottpalegg_1"],
        "Kyllingpålegg": categories["kyllingpalegg_3"],
        "Spekemat": categories["spekemat_1"],
        "Salami": categories["salami_3"],
        "Leverpostei": categories["leverpostei_2"],
        "Salatpålegg": categories["paleggsalat_1"],
        "Syltetøy": categories["syltetoy_1"],
        "Gele": categories["gele"],
        "Marmelade": categories["marmelade"],
        "Majones": categories["majones_1"],
        "Tubepålegg": categories[
            "tubepalegg"
        ],  # TODO Smøreost, kaviar, makrell i tomat på tube ??
        "Ost i skiver": categories["ost_0"],
        "['Pålegg', 'Gulost']": categories["gulost_2"],
        "['Pålegg', 'Brunost']": categories["brunost_1"],
        "['Pålegg', 'Smøreost og prim']": categories["smoreoster_1"],
        "Honning og sirup": categories["honning-sirup"],
        "Søtpålegg": categories["sotpalegg_1"],
        # MIDDAGER OG TILBEHØR
        "Ferdige middagsretter": categories["ferdigmaltid_2"],
        "Grøt": categories["grot_1"],
        "Ferdigsupper": categories["supper_1"],
        "Middags-kit og gryteretter": categories["middag-kit_1"],
        "Posesupper": categories["posesupper"],
        "Middagshermetikk": categories["middagshermetikk_1"],
        "Middagstilbehør": categories["middagstilbehor_0"],
        "Posesauser": categories["posesauser"],
        "Ferdigsauser": categories["ferdigsauser"],
        "Fond": categories["kraft-og-buljong_1"],
        "Ris": categories["ris_2"],
        "Bulgur og quinoa": categories["bulgur-quinoa"],
        "Couscous": categories["couscous_2"],
        "Linser": categories["linser_2"],
        "Fersk pasta": categories["fersk-pasta"],
        "Pasta": categories["pasta_1"],
        "Nudler": categories["nudler_1"],
        "Fersk pizza": categories["pizza_2"],  # TODO Need own subcat ??
        "Fryst pizza": categories["pizza_2"],  # TODO Need own subcat ??
        "Pizzasaus": categories["pizzasaus_2"],
        "Pizzamelblanding": categories["pizzabunnmix_2"],
        "Pizzabunn": categories["pizzabunn_2"],
        "Pizzafyll": categories["pizzasaus_2"],  # Weird category
        "Tortillalefser": categories["tortillalefser_2"],
        "Tacoskjell": categories["tacoskjell_2"],
        "Tortillachips": categories["tortillachips_2"],
        "Tacokit": categories["tacokit_2"],
        "Tacosaus": categories["tacosaus_2"],
        "Tacokrydder og topping": categories["tacokryddermix_2"],
        "Dim sum": categories["ferdigmaltider_1"],  # TODO Need own subcat ??
        "Vårruller": categories["varruller"],
        "Indisk": categories["asiatiske-sauser_2"],  # TODO Need own subcat ??
        "Wok": categories["woksaus_3"],  # TODO Need own subcat ??
        "Sushi": categories["sushi_1"],
        "Soyasaus, chilisaus og paste": categories["sojasaus-chilisaus-paste"],
        "Kokosmelk": categories["kokosmelk_1"],
        "Ketchup og sennep": categories["ketchup-og-sennep_1"],
        "Majonesbaserte sauser": categories["majonesbaserte-sauser"],
        "Dressinger": categories["dressinger_1"],
        "Tsatziki og hummus": categories["tsatziki-hummus"],
        "Oljer": categories["matoljer_1"],
        "Eddik": categories["eddiker_1"],
        "Salt og pepper": categories["salt-og-pepper_1"],
        "Krydder": categories["krydder_1"],
        "Spicemix": categories["kryddermix_2"],
        "Buljong og fond": categories["kraft-og-buljong_1"],
        "Marinader": categories["marinade_2"],
        # DRIKKE
        "Stillvann": categories["vann_2"],
        "Vann med kullsyre": categories["vann-med-kullsyre_2"],
        "Brus med sukker": categories["brus-med-sukker"],
        "Sukkerfri brus": categories["brus-uten-sukker"],
        "Energidrikker": categories["energidrikk_1"],
        "Sport- og vitamindrikker": categories["sports-vitamindrikker"],
        "Appelsinjuice": categories["appelsinjuice"],
        "Eplejuice": categories["eplejuice"],
        "Grønnsaksjuice": categories["gronnsaksjuice"],
        "Juice shot": categories["juice-shot"],
        "Frukt- og bærjuice": categories["frukt-brjuice"],
        "Kombucha og vannkefir": categories["kombucha_1"],  # TODO Need own subcat ??
        "Smoothie": categories["smoothie_1"],
        "Saft med sukker": categories["saft-med-sukker"],
        "Sukkerfri saft": categories["saft-uten-sukker"],
        "Filterkaffe": categories["filtermalt-kaffe_2"],
        "Hele kaffebønner": categories["hele-kaffebonner_2"],
        "Presskanne": categories["presskannemalt-kaffe_2"],
        "Kokmalt": categories["kokmalt-kaffe_2"],
        "Kaffekapsler": categories["kaffekapsler_1"],
        "Pulverkaffe": categories["instant-kaffe_2"],
        "Smakskaffe": categories["smakskaffe"],
        "Kaffefilter og tilbehør": categories["kaffefilter-tilbehor"],
        "Iskaffe": categories["iskaffe_1"],
        "Iste": categories["iste_1"],
        "Sort te": categories["sort-te"],
        "Grønn te": categories["gronn-te"],
        "Urte-te og frukt-te": categories["urtete-fruktte"],
        "Kakao": categories["sjokoladedrikk_1"],  # TODO Need own subcat ??
        "Sjokoladepulver": categories["sjokoladedrikk_1"],  # TODO Need own subcat ??
        "Øl": categories["ol_2"],
        "Lettøl": categories["lettol_2"],
        "Spesialøl og import": categories["spesialol"],
        "Alkoholfritt øl": categories["alkoholfritt-ol_2"],
        "Cider": categories["cider_2"],
        "Ferdigdrink": categories["ferdigdrink_1"],
        "Alkoholfri cider og ferdigdrink": categories["alkoholfri-cider_2"],
        "Blandevann": categories["blandevann"],
        "Drinkmiks": categories["drinkmiks"],
        # BAKEINGREDIENSER
        "Fint mel": categories["fint-mel"],
        "Grovt mel": categories["grovt-mel"],
        "Pizzamel": categories["pizzamel"],
        "Matlagningsmel": categories["matlagningsmel"],
        "Sukker": categories["sukker_1"],
        "Sirup": categories["sirup_2"],
        "Søtningsmidler": categories["sotningsstoff_2"],
        "Gjær": categories["gjr_1"],
        "Hevemidler": categories["hevemidler"],
        "Kaker": categories["kakemiks"],
        "Brød og rundstykker": categories["brod-rundstykke-miks"],
        "Boller": categories["bollemix_2"],
        "Pannekaker og vaffler": categories["pannekake-vafler-miks"],
        "Dessert": categories["dessertmiks"],
        "Pizza": categories["pizzabunnmix_2"],
        "Kakepynt": categories["kakepynt_2"],
        "Kakefyll": categories["kakekrem_2"],
        "Kokesjokolade": categories["kokesjokolade_2"],
        "Baketilbehør": categories["baking_1"],  # TODO Need own subcat ??
        # ISKREM DESSERTER OG KAKER
        "Fløteis": categories["dessertis_2"],
        "Sorbet": categories["sorbet"],
        "['Porsjonsis', 'Fløteis']": categories["smais-multipack_2"],
        "Saftis": categories["smais-multipack_2"],  # TODO Need own subcat ??
        "Gelé": categories["gele_1"],
        "Puddinger": categories["dessertpuddinger_1"],
        "Sauser og toppinger": categories["dessertsauser_1"],
        "Riskrem": categories["riskrem_1"],
        "Hermetisert frukt og kompott": categories["hermetisert-frukt-kompott"],
        "Kaker": categories["kaker_1"],
        "Lefser": categories["lefser_1"],
        # SNACKS OG GODTERI
        "Chips": categories["chips_2"],
        "Snacks": categories["snacks_1"],
        "Popcorn": categories["popcorn_1"],
        "Dip": categories["dip_1"],
        "Sjokoladeplater": categories["sjokoladeplater"],
        "Sjokoladebarer": categories["sjokoladebarer"],
        "Sjokoladeblandinger": categories["sjokoladeblandinger"],
        "Premium sjokolade": categories["premium-sjokolade"],
        "Godteri": categories["godteri_1"],
        "Peanøtter": categories["peanotter_2"],
        "Cashewnøtter": categories["cashewnotter_2"],
        "Nøtteblanding": categories["notteblanding_2"],
        "Tyggegummi": categories["tyggegummi_1"],
        "Pastiller": categories["pastiller_1"],
        "Cookies": categories["cookies_2"],
        "Søtkjeks": categories["sotkjeks_2"],
        "Kjeks til ost": categories["smorbrodkjeks_2"],
        # BABY OG BARN
        "Buksebleier": categories["buksebleier"],
        "Svømmebleier": categories["badebleier_1"],
        "Åpne bleier": categories["apne-bleier"],
        "Nattbleier": categories["nattbleier"],
        "Middagsglass": categories["middagsglass"],
        "Pulvergrøt": categories["pulvergrot"],
        "Ferdiggrøt": categories["ferdiggrot"],
        "Smoothie": categories["barnesmoothie"],
        "Yoghurt": categories["barneyoghurt"],
        "Snacks": categories["barnesnacks"],
        "Drikke": categories["barnedrikke"],
        "Drikkeklar": categories["morsmelk-drikkeklar"],
        "Pulver": categories["morsmelk-pulver"],
        "Våtservietter og ammeinnlegg": categories["vatservietter_2"],
        "Såpe og babyolje": categories["sape-babyolje"],
        "Babypleie": categories["babypleie_1"],
        "Babytannpleie": categories["babytannpleie"],
        "Helseprodukter for barn": categories["barnehelse"],
        "Bursdag": categories["sesong-og-fest_1"],
        "Smokker": categories["smokker_2"],
        "Flasker og kopper": categories["tateflaske_2"],  # TODO Need own subcat ??
        "Matbokser og smekker": categories[
            "barneprodukter_0"
        ],  # TODO Need own subcat ??
        "Nyttig til barn": categories["barneprodukter_0"],  # Weird category ??
        "Spill og leker": categories["barneprodukter_0"],  # TODO Need own subcat ??
        "Barneklær": categories["barneprodukter_0"],  # TODO Need own subcat ??
        "Tilbehør vogn": categories["barneprodukter_0"],  # TODO Need own subcat  ??
        # LEGEMIDLER HELSEKOST OG TRENING
        "Legemidler": categories["legemidler"],
        "Plaster": categories["plaster_2"],
        "Vitaminer og kosttilskudd": categories["vitaminer-kosttilskudd"],
        "Vektkontroll": categories["vektkontroll"],
        "Nikotinprodukter": categories["roykeslutt_2"],
        "Sportsdrikke": categories["sportsdrikke"],
        "Måltidserstatter og mellommåltid": categories["maltidserstatter-mellommaltid"],
        "Proteinpulver": categories["proteinpulver"],
        "Protein- og müslibarer": categories["protein-muslibarer"],
        # HYGIENE OG SKJØNNHET
        "Håndsåpe": categories["handsape_3"],
        "Dusjsåpe": categories["dusjsape_3"],
        "Intimsåpe": categories["intimvask_2"],
        "Barnesåpe og babyolje": categories["sape-babyolje"],
        "Intimsåpe": categories["intimvask_2"],
        "Shampo og hårprodukter": categories["shampo-harprodukter"],
        "Hårfarge": categories["harfarge_2"],
        "Hårstyling": categories["harstyling"],
        "Hårfarge": categories["harfarge_2"],
        "Ansiktspleie": categories["ansiktspleie_2"],
        "Bodylotion": categories["bodylotion_2"],
        "Leppomade": categories["leppepomade_2"],
        "Solkrem og selvbruning": categories["solkrem_2"],
        "Ansiktsrens": categories["sminkefjerner_2"],
        "Tannkrem": categories["tannkrem_2"],
        "Tannbørster": categories["tannborste_2"],
        "Tanntråd og tannpirkere": categories["tanntrad-tannpirkere"],
        "Munnskyll og fluortabletter": categories["munnskyll-fluortabletter"],
        "Deodoranter": categories["deodorant_2"],
        "Bomull": categories["bomull"],
        "Barbering": categories["barbering_1"],
        "Prevensjon": categories["prevensjon"],
        "Bind": categories["bind_2"],
        "Truseinnlegg": categories["truseinnlegg_2"],
        "Tamponger": categories["tamponger_2"],
        "Menskopper": categories["bind-og-tamponger_1"],
        "Mascara": categories["sminke"],  # TODO Need own subcat
        "Øyenskygge, liners og bryn": categories["sminke"],  # TODO Need own subcat
        "Leppestift, liner og gloss": categories["sminke"],  # TODO Need own subcat
        "Foundation og pudder": categories["sminke"],  # TODO Need own subcat
        "Neglelakk og neglelakkfjerner": categories["sminke"],  # TODO Need own subcat
        # HUS OG HJEM
        "Rengjøringsmidler": categories["rengjoringsmiddel_2"],
        "Oppvaskmidler": categories["oppvaskmiddel_2"],
        "Klesvask": categories["klesvask_1"],
        "Kluter, svamper og hansker": categories["kluter-svamper-hansker"],
        "Toalettpapir": categories["toalettpapir_2"],
        "Tørkerull": categories["torkerull_2"],
        # Skipped some categories here
        # BLOMSTER OG PLANTER
        "Snittblomster": categories["blomster_1"],
        "Planter": categories["potteplanter_1"],
        "Potter": categories["blomster-og-planter_0"],
        "Vaser": categories["blomster-og-planter_0"],
        "Plantenæring og frø": categories["plantenring_1"],
        # DYR
        "['Hundemat', 'Våtfôr']": categories["hundemat_1"],
        "['Hundemat', 'Tørrfôr']": categories["hundemat_1"],
        "['Hundemat', 'Snacks']": categories["hundemat_1"],
        "['Hundemat', 'Faghandel']": categories["hundemat_1"],
        "['Kattemat', 'Våtfôr']": categories["kattemat_1"],
        "['Kattemat', 'Tørrfôr']": categories["kattemat_1"],
        "['Kattemat', 'Snacks']": categories["kattemat_1"],
        "['Kattemat', 'Faghandel']": categories["kattemat_1"],
        "Fuglemat": categories["fuglemat_1"],
        "Gnagermat": categories["gnagermat"],
        "Dyreutstyr": categories["dyreartikler_1"],
        # SNUS OG TOBAKK
        "Snus": categories["snus_1"],
        "Sigaretter": categories["sigaretter_1"],
        "Rulletobakk": categories["tobakk_1"],
        "Skråtobakk": categories["tobakk_1"],
        # DONE
    },
    "coop": {
        # FRUKT OG GRØNT
        "Grønnsaker": categories["gronnsaker_1"],
        "Hermetiske grønnsaker": categories["hermetisk-gront_1"],
        "Frukt": categories["frukt_1"],
        "Grønnsaksblanding": categories["frosne-br-og-gronnsaker_1"],
        "Bær": categories["br_1"],
        "Poteter": categories["poteter_1"],
        "Hermetisk frukt": categories["hermetisk-frukt-og-br_1"],
        "Krydderurter": categories["krydderurter_1"],
        "Sopp": categories["sopp_2"],
        # FROKOST
        "Kjøttpålegg": categories["kjottpalegg_1"],
        "Spekemat": categories["spekemat_1"],
        "Postei og pate": categories["postei-og-pate_1"],
        "Syltetøy": categories["syltetoy_1"],
        "Fiskepålegg": categories["fiskepalegg_1"],
        "Majones og remulade": categories["majones-remulade"],
        "Søtpålegg": categories["sotpalegg_1"],
        "Påleggsalat": categories["paleggsalat_1"],
        "Frokostblanding": categories["frokostblandinger-og-musli_1"],
        # EGG
        "Egg": categories["egg_1"],
        # MEIERIPRODUKTER
        "Hvitost": categories["gulost_2"],
        "Smøreost": categories["smoreost_2"],
        "Revet ost": categories["revet-ost_1"],
        "Fersk ost": categories["fersk-ost"],
        "Brunost": categories["brunost_1"],
        "Myk ost": categories["myk-ost"],
        "Blåmuggost": categories["blamuggost_1"],
        "Fast ost": categories["parmesan-og-smaksrike-fastoster_1"],
        "Søst": categories["sost"],
        "Ost diverse": categories["ost_0"],
        "Pultost": categories["pultost_1"],
        "Gammelost": categories["gamalost_1"],
        "Yoghurt": categories["yoghurt_2"],
        "Smør og margarin": categories["smor-og-margarin_1"],
        "Melk": categories["melk_1"],
        "Fløte og rømmeprodukter": categories["flote-rommeprodukter"],
        "Syrnet melk": categories["syrnet-melk"],
        "Drikker": categories["melk-med-smak"],
        # KYLLING OG KJØTT
        "Kylling og kalkun": categories["kylling-og-fjrkre_0"],
        "Kjøttdeig og farse": categories["kjottdeig-og-farse_1"],
        "Pølser": categories["polser_1"],
        "Bacon": categories["bacon_1"],
        "Svin": categories["svinekjott_1"],
        "Kjøttkaker og karbonader": categories["kjottboller-karbonader"],
        "Storfe": categories["storfekjott_1"],
        "Hamburger": categories["hamburger_1"],
        "Sau og lam": categories["lammekjott_1"],
        # FISK OG SKALLDYR
        "Fisk": categories["fisk_1"],
        "Fiskemat": categories["fiskeretter_1"],
        "Skalldyr": categories["skalldyr_1"],
        "Reker": categories["reker_1"],
        # MIDDAG OG TILBEHØR
        "Ferdigretter": categories["ferdigmaltider_1"],
        "Supper, sauser og gryter": categories[
            "middagstilbehor_0"
        ],  # TODO Need own subcat
        "Pasta og nudler": categories["pasta-nudler"],
        "Pastasaus": categories["pastasaus_2"],
        "Taco": categories["taco_1"],
        "Pizza": categories["pizza_1"],
        "Krydder, salt og eddik": categories[
            "middagstilbehor_0"
        ],  # TODO Need own subcat
        "Ketchup, sennep og dressing": categories[
            "middagstilbehor_0"
        ],  # TODO Need own subcat
        "Wok": categories["asiatiske-sauser_2"],  # TODO Need own subcat ??
        "Indisk": categories["currysaus_3"],  # TODO Need own subcat
        "Thai": categories["asiatiske-sauser_2"],  # TODO Need own subcat
        "Sushi": categories["sushi_1"],
        "Middagshermetikk": categories["middagshermetikk_1"],
        "Ris og gryn": categories["ris_1"],  # TODO Need own subcat
        "Rissaus": categories["asiatiske-sauser_2"],
        "Middagstilbehør": categories["middag_0"],  # TODO Need own subcat
        "Hurtigmat": categories["ferdigmaltid_2"],
        "Middags-kits": categories["middag-kit_1"],
        # VEGETAR
        "Vegetar": categories["vegetarretter_1"],
        # BAKEVARER
        "Rundstykker og småbakst": categories["rundstykker-og-smabrod_1"],
        "Ferske brød": categories["brod_1"],
        "Knekkebrød": categories["knekkebrod_1"],
        "Lomper, pølse- og hamburgerbrød": categories[
            "bakeri_0"
        ],  # TODO Need own subcat
        "Fryste brød": categories["brod_1"],  # TODO Need own subcat
        # BAKING
        "Nøtter og tørket frukt": categories["torket-frukt-og-notter_1"],
        "Mel og gryn": categories["mel-og-gryn_1"],
        "Bakeartikler": categories["baking_1"],
        "Matolje": categories["matoljer_1"],
        "Ferdigmixer": categories["bakemixer_1"],
        "Sukker og søtning": categories["sukker_1"],  # TODO Need own subcat
        "Kakao og marsipan": categories["baking_1"],  # TODO Need own subcat
        # BABY OG BARN
        "Babyartikler": categories["babyartikler_1"],
        "Matglass": categories["middagsglass"],
        "Barnegrøt": categories["barnegrot_1"],
        "Barnedessert": categories["barnedessert_1"],
        "Klemmeposer": categories["barnemat_1"],  # TODO Need own subcat
        "Babysnacks": categories["barnesnacks"],
        "Bleier": categories["bleier_1"],
        "Morsmelkerstatning": categories["morsmelkerstatning_1"],
        # DRIKKEVARER
        "Brus": categories["brus_1"],
        "Juice og nektar": categories["juice_1"],
        "Kaffe": categories["kaffe_1"],
        "Saft": categories["saft_1"],
        "Energidrikk": categories["energidrikk_1"],
        "Vann": categories["vann_1"],
        "Te": categories["te_1"],
        "Drikke Alkoholfri": categories["drikke_0"],  # TODO Need own subcat
        "Iskaffe": categories["iskaffe_1"],
        "Sjokolade og toddy": categories["drikke_0"],  # TODO Need own subcat
        "Iste": categories["iste_1"],
        "Smoothie": categories["smoothie_1"],
        # KAKER KJEKS OG DESSERT
        "Kjeks og cookies": categories["kjeks_1"],
        "Kaker": categories["kaker_1"],
        "Pudding og mousse": categories["dessertpuddinger_1"],
        "Dessertsaus og topping": categories["dessert_0"],  # TODO Need own subcat
        "Gele": categories["gele_1"],
        "Smådesserter": categories["smadesserter_1"],
        # SNACKS OG GODTERI
        "Sjokolade": categories["sjokolade_1"],
        "Chips": categories["chips_2"],
        "Godteri": categories["godteri_1"],
        "Snacks": categories["snacks_1"],
        "Drops og pastiller": categories["pastiller_1"],
        "Nøtter": categories["notter_1"],
        "Tyggegummi": categories["tyggegummi_1"],
        "Popcorn": categories["popcorn_1"],
        # HYGIENEARTIKLER
        "Såper": categories["saper_2"],
        "Tannpleie": categories["tannpleie_1"],
        "Hårpleie": categories["harpleie_1"],
        "Bind og tamponger": categories["bind-og-tamponger_1"],
        "Solkrem": categories["solkrem_2"],
        "Hudpleie": categories["hudpleie_1"],
        "Deodorant": categories["deodorant_2"],
        "Lommetørkle og bomullpads": categories[
            "personlig-hygiene_1"
        ],  # TODO Need own subcat
        "Hårfjerning": categories["harfjerningsprodukter_2"],
        "Kosmetikk": categories["sminke"],
        "Hårfarge": categories["harfarge_2"],
        "Intimservietter og vask": categories[
            "personlig-hygiene_1"
        ],  # TODO Need own subcat
        # APOTEKVARER OG HELSEKOST
        "Kosttilskudd": categories["kosttilskudd_2"],
        "Sårpleie": categories["apotekvarer_1"],  # TODO Need own subcat
        "Prevensjon og graviditet": categories["prevensjon"],
        # HUS OG HJEM
        "Oppvask og renhold": categories["renhold_1"],  # TODO Need own subcat
        "Klesvask": categories["klesvask_1"],
        "Toalettpapir og tørk": categories["renhold_1"],  # TODO Need own subcat
        "Poser og folie": categories["poser-papir-og-folie_1"],
        "Engangsservise og servietter": categories[
            "borddekning_1"
        ],  # TODO Need own subcat
        "Batterier": categories["batterier_3"],
        "Stearinlys og tenning": categories["stearinlys_2"],  # TODO Need own subcat
        "Lyspærer og lysrør": categories["lyspre_3"],
        "Avfallsekker og poser": categories["avfallssekker_2"],
        "Engangsgrill": categories["engangsgrill_2"],
        # DYR
        "Kattemat": categories["kattemat_1"],
        "Hundemat": categories["hundemat_1"],
        "Dyreutstyr og leker": categories["dyreartikler_1"],
        "Fuglemat": categories["fuglemat_1"],
        # DONE
    },
}


def extract_categories(offer: MpnOffer, config: HandleConfig) -> Union[dict, None]:
    try:
        categories_field: str = pydash.get(config, ["categoriesField"], "categories")
        last_two_categories = str(offer[categories_field][-2:])
        last_category = offer[categories_field][-1]
        dealer = offer["dealer"]
        category = None
        if dealer == "meny":
            cat_key = f"{last_category}_{len(offer[categories_field])-1}"
            category = categories.get(cat_key)
        else:
            category = pydash.get(category_mappings, [dealer, last_two_categories])
            if not category:
                category = pydash.get(category_mappings, [dealer, last_category])
        result = []
        current_cat = category
        while current_cat:
            result.insert(0, current_cat)
            current_cat = categories.get(current_cat["parent"])
        return result
    except Exception as e:
        return None
