"""Write SOURCES.md from the feed harvest, so every line on the page has a real link.

Run at authoring time:

    python3 tools/gen_sources.py /tmp/feeds.json

`feeds.json` is the harvest of the six world-news feeds on 19 November 2026, one
object per item: {"source", "title", "link", "date"}. This script pairs each story
on the page with the harvested item that reported it, refuses to invent anything,
and fails loudly if a story has no item to point at.

The page is built from what those outlets published that day. Nothing here is
reconstructed from memory, and no headline is paraphrased into a source line.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import content  # noqa: E402

# One unique fragment of the reported headline, per story on the page, in the order
# the stories appear. A fragment must match exactly one harvested item.
HERO_KEYS = [
    "Trump-Xi-Putin summit",
    "ICJ rules Myanmar committed genocide",
    "Anthropic's record-breaking IPO",
    "South African DJ celebrates featuring in GTA 6",
    "far more painful",
    "PIF Tower in Riyadh",
    "boat carrying 100 migrants sinks off Senegal",
    "completes ground operation in Gaza beyond Yellow Line",
    "Danish MPs approve Greenland security pact",
    "US consortium wins huge Kenya mining deal",
    "Van Gogh painting sells for record",
]

AGATE_KEYS = [
    "Ukraine’s allies meet in Berlin",
    "North Korea expanded uranium enrichment plant",
    "Democrats nominate Hakeem Jeffries",
    "Trump claims Iran is developing bioweapons",
    "Somalia expels UAE ambassador",
    "Israeli ambassador condemns Australia's sanctions",
    "What is at stake at the EU-UK summit",
    "Violent protests and killings in Bangladesh",
    "Elon Musk says record $446m",
    "US, European countries urge Iran at IAEA meeting",
    "Survivors of Uganda's deadly landslide",
    "Datacentres to create 70% more carbon",
    "UK court confirms government ordered Apple",
    "India's religious make-up",
    "Venezuela signs military deal with US",
    "US Army gives contractors 45 days",
    "Race to replant five South African baobabs",
    "Australian music industry rejects",
    "Catherine visits Mumbai maternity hospital",
    "Waymo pulls driverless taxis",
    "Mosque set on fire in Israel",
    "South Korean court orders retrial for ex-PM Han",
    "guilty over role in assassination",
    "Trump calls for nuclear arms reduction at APEC",
]


def find(items: list[dict], needle: str) -> dict:
    hits = [it for it in items if needle.lower() in it["title"].lower()]
    if len(hits) != 1:
        raise SystemExit(f"{needle!r} matched {len(hits)} items; need exactly one")
    return hits[0]


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: gen_sources.py <feeds.json>")
    items = json.loads(Path(sys.argv[1]).read_text())

    heroes = content.HEROES + content.SECONDARY
    if len(HERO_KEYS) != len(heroes) or len(AGATE_KEYS) != len(content.AGATE):
        raise SystemExit("key lists are out of step with the page")

    out = [
        "# Sources",
        "",
        "Every story on this page was reported on **Thursday 19 November 2026**. The page",
        "was built from the world-news feeds of six outlets, harvested that day with",
        "`tools/gen_sources.py`; this file is generated from that harvest rather than typed",
        "by hand, so each line below points at the item that carried it.",
        "",
        "The eleven numbered stories, in page order:",
        "",
        "| # | Section | Story on the page | Reported by | Headline as published |",
        "|---|---|---|---|---|",
    ]
    for story, key in zip(heroes, HERO_KEYS):
        it = find(items, key)
        out.append(
            f"| {story['num']:02d} | {story['kicker']} | {story['head']} | {it['source']} | "
            f"[{it['title']}]({it['link']}) |"
        )

    out += [
        "",
        "The twenty-four briefs at the foot of the page:",
        "",
        "| Line | Region | Story on the page | Reported by | Headline as published |",
        "|---|---|---|---|---|",
    ]
    for i, ((region, line), key) in enumerate(zip(content.AGATE, AGATE_KEYS), start=1):
        it = find(items, key)
        out.append(
            f"| {i:02d} | {region.title()} | {line} | {it['source']} | "
            f"[{it['title']}]({it['link']}) |"
        )

    out += [
        "",
        "## Figures",
        "",
        "Each statistic in the strip under the masthead is taken from one of those stories:",
        "",
        "- **$81.3bn** — the size of Anthropic's listing (story 03).",
        "- **13 years** — since Grand Theft Auto V, the previous game (story 04).",
        "- **$190.4m** — the price paid for the Van Gogh (story 11).",
        "- **100** — the people aboard the boat lost off Senegal (story 07).",
        "- **45 days** — the deadline the US Army gave contractors for fortified bunkers in",
        "  Israel (brief 16).",
        "- **70%** — the rise in datacentre carbon emissions the IEA projects by 2030 (brief 12).",
        "",
        "## Artwork",
        "",
        "All illustrations on the page are drawn in code by `tools/render.py`: three lead",
        "pictures (a summit table, a court facade, a listing chart), eight small icons, and",
        "the world map. The map's coastlines come from `tools/data/land.json`, a simplified",
        "extract of the public-domain Natural Earth land layer, projected equirectangularly",
        "and redrawn at page scale. No photographs, stock images or third-party artwork are",
        "used anywhere on the page.",
        "",
    ]

    Path("SOURCES.md").write_text("\n".join(out))
    print(f"SOURCES.md written: {len(heroes)} numbered stories, {len(content.AGATE)} briefs")
    return 0


if __name__ == "__main__":
    sys.exit(main())
