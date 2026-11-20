"""The day's news of Thursday 19 November 2026, as it goes on the page.

Every line below was reported, or first published, on 19 November 2026. `SOURCES.md`
names the outlet, headline and URL for each. Region tags are the six inhabited
continents; the `pin` tuple is (longitude, latitude) of the place the story happened.
"""

DATE = "THURSDAY 19 NOVEMBER 2026"
DAY_WORD = "THURSDAY"
NAME = "THE WORLD IN ONE DAY"

# Six figures that belong to six different stories, so the rail never repeats a card.
FIGURES = [
    ("$81.3bn", "Anthropic's listing, the largest ever"),
    ("13 years", "between Grand Theft Auto games"),
    ("$190.4m", "paid for a Van Gogh at auction"),
    ("100", "aboard the boat lost off Senegal"),
    ("45 days", "US army deadline for Israel bunkers"),
    ("70%", "extra datacentre carbon by 2030"),
]

# Three lead stories: art panel, kicker, headline, deck, map pin.
HEROES = [
    {
        "num": 1,
        "region": "ASIA",
        "place": "Shenzhen",
        "kicker": "APEC \u00b7 CHINA",
        "head": "Trump, Xi and Putin sit down together for the first time",
        "deck": "An unscheduled trilateral session at the Pacific summit put the three "
                "nuclear powers in one room; the host called it the week's real result.",
        "detail": ["An unscheduled session, added to the summit programme the night before",
                   "Three nuclear powers, one room, one table",
                   "The host called it the week's real result"],
        "pin": (114.1, 22.5),
        "art": "summit",
    },
    {
        "num": 2,
        "region": "ASIA",
        "place": "The Hague",
        "kicker": "WORLD COURT \u00b7 MYANMAR",
        "head": "Judges find Myanmar committed genocide against the Rohingya",
        "deck": "The ICJ ruling is the first by the UN's top court to hold a state "
                "responsible for genocide against the Muslim minority.",
        "pin": (4.3, 52.1),
        "art": "court",
    },
    {
        "num": 3,
        "region": "AMERICAS",
        "place": "New York",
        "kicker": "MARKETS \u00b7 ANTHROPIC",
        "head": "Anthropic raises $81.3bn in the biggest listing on record",
        "deck": "The AI developer's debut on the Nasdaq dwarfs every previous float, "
                "and makes it one of the most valuable companies in the world.",
        "pin": (-74.0, 40.7),
        "art": "markets",
    },
]

# Eight second-rank stories: one icon, a headline and a single deck line each.
SECONDARY = [
    {
        "num": 4, "region": "OCEANIA", "kicker": "CULTURE \u00b7 WORLDWIDE", "place": "Sydney",
        "head": "GTA VI arrives, thirteen years after the last one",
        "deck": "Queues from Miami to Sydney; a South African DJ called his cameo a dream come true.",
        "pin": (151.2, -33.9), "icon": "game",
    },
    {
        "num": 5, "region": "EUROPE", "kicker": "UKRAINE \u00b7 CRIMEA", "place": "Kerch",
        "head": "Bridge hit again, and Putin vows a 'far more painful' reply",
        "deck": "Strikes damaged the road span; Moscow promised retaliation against Kyiv's backers.",
        "pin": (36.5, 45.3), "icon": "bridge",
    },
    {
        "num": 6, "region": "MIDDLE EAST", "kicker": "SAUDI ARABIA \u00b7 HOUTHIS", "place": "Riyadh",
        "head": "Missile debris damages the PIF Tower in Riyadh's financial district",
        "deck": "Air defences intercepted a Houthi missile aimed at the capital, Saudi officials said.",
        "pin": (46.7, 24.7), "icon": "missile",
    },
    {
        "num": 7, "region": "AFRICA", "kicker": "MIGRATION \u00b7 SENEGAL", "place": "Dakar",
        "head": "Dozens missing after a boat carrying 100 migrants sinks off Senegal",
        "deck": "Coastguard boats and fishing crews pulled survivors from the Atlantic through the day.",
        "pin": (-17.4, 14.7), "icon": "boat",
    },
    {
        "num": 8, "region": "MIDDLE EAST", "kicker": "GAZA \u00b7 CEASEFIRE", "place": "Gaza",
        "head": "Israeli tanks cross the Yellow Line into central Gaza",
        "deck": "The army said its ground operation beyond the boundary was complete.",
        "pin": (34.4, 31.4), "icon": "tank",
    },
    {
        "num": 9, "region": "EUROPE", "kicker": "ARCTIC \u00b7 DENMARK", "place": "Copenhagen",
        "head": "Danish MPs approve a Greenland security pact with Washington",
        "deck": "The vote hands the US a wider military footing on the island.",
        "pin": (12.6, 55.7), "icon": "ice",
    },
    {
        "num": 10, "region": "AFRICA", "kicker": "MINING \u00b7 KENYA", "place": "Nairobi",
        "head": "A US consortium wins Kenya's biggest mining deal, beating Chinese bidders",
        "deck": "The award covers a rare-earths deposit the government calls strategic.",
        "pin": (36.8, -1.3), "icon": "mine",
    },
    {
        "num": 11, "region": "EUROPE", "kicker": "ART \u00b7 LONDON", "place": "London",
        "head": "A Van Gogh sells for a record $190.4m after a restitution row",
        "deck": "The price is the highest paid for a work at auction this year.",
        "pin": (-0.1, 51.5), "icon": "art",
    },
]

# The agate index: breadth without crowding the cards, one line each.
AGATE = [
    ("EUROPE", "Allies meet in Berlin on air defence and money"),
    ("ASIA", "IAEA: North Korea expanding uranium plant"),
    ("AMERICAS", "Jeffries near first Black speakership"),
    ("MIDDLE EAST", "Trump: Iran seeking chemical weapons"),
    ("AFRICA", "Somalia expels the UAE ambassador"),
    ("OCEANIA", "Israel warns Australia of reciprocal measures"),
    ("EUROPE", "EU and UK summit in Brussels: what is at stake"),
    ("ASIA", "Bangladesh protests before Hasina's return"),
    ("AMERICAS", "Musk: $446m midterm spending 'pretty foolish'"),
    ("MIDDLE EAST", "US presses Iran to readmit UN inspectors"),
    ("AFRICA", "Uganda landslide survivors take case to the UN"),
    ("WORLD", "IEA: datacentres to add 70% more carbon by 2030"),
    ("EUROPE", "Court confirms UK ordered Apple to break encryption"),
    ("ASIA", "Pew study maps India's religious make-up"),
    ("AMERICAS", "Venezuela signs a military deal with the US"),
    ("MIDDLE EAST", "Army gives builders 45 days for Israel bunkers"),
    ("AFRICA", "Five baobabs replanted after export blocked"),
    ("OCEANIA", "Australian music industry split on AI scraping"),
    ("ASIA", "Catherine visits a Mumbai maternity hospital"),
    ("AMERICAS", "Waymo pauses driverless taxis on freeways"),
    ("MIDDLE EAST", "Mosque set on fire in Israel; leaders trade blame"),
    ("ASIA", "South Korea court orders retrial of ex-PM Han"),
    ("AMERICAS", "Pastor guilty over Haiti assassination plot"),
    ("ASIA", "Trump calls for nuclear arms cuts at APEC"),
]

CONTINENTS = 6


def story_count() -> int:
    return len(HEROES) + len(SECONDARY) + len(AGATE)
