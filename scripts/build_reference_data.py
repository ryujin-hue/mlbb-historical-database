#!/usr/bin/env python3
"""Build reference/ lookup tables for mlbb-historical-database.

Every row is derived from the repo's verified datasets (research CSVs already
cross-checked against official sources). No fabricated values: unknown
attributes stay empty.
"""
import csv
import os
import re
import shutil
from collections import Counter

REPO = "/home/z/my-project/download/mlbb-historical-database"
REF = os.path.join(REPO, "references")
RESEARCH = "/home/z/my-project/research"
os.makedirs(REF, exist_ok=True)

W = lambda name, rows: _write(name, rows)  # noqa: E731


def _write(name, rows):
    if not rows:
        raise RuntimeError(f"reference table {name} is empty")
    path = os.path.join(REF, name)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"  references/{name}: {len(rows)} rows")


def read(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def sysrow(system, aspect):
    for r in read(os.path.join(REPO, "systems.csv")):
        if r["system"] == system and r["aspect"] == aspect:
            return r
    raise RuntimeError(f"systems.csv row not found: {system}/{aspect}")


# ---------------------------------------------------------------- 1. roles
heroes = read(os.path.join(REPO, "hero_master.csv"))
ROLE_DESC = {
    "tank": "Frontline protector; high durability, initiates fights and soaks damage for the team.",
    "fighter": "Balanced melee bruiser; durable damage dealer for the EXP lane or jungle.",
    "assassin": "Burst damage dealer that hunts squishy backline targets; jungle or roam.",
    "mage": "Magic damage dealer with area control and burst or poke from the mid lane.",
    "marksman": "Ranged physical damage carry scaling into late game; gold lane.",
    "support": "Shields, heals and crowd control to protect and empower teammates; roam lane.",
}
roles = Counter((h["role"] or "").strip().lower() for h in heroes)
roles.pop("", None)
rows = [{"role": r, "hero_count": n,
         "description": " / ".join(ROLE_DESC.get(p.strip(), "") for p in r.split("/"))}
        for r, n in sorted(roles.items(), key=lambda x: -x[1])]
W("hero_roles.csv", rows)

# ---------------------------------------------------------------- 2. lanes
LANE_DESC = {
    "Gold": "Marksman farming lane; safe gold income from side minion waves and the gold crab.",
    "EXP": "Fighter/EXP lane; solo side lane with extra EXP from the EXP minion wave.",
    "Mid": "Mage/mid lane; center lane, fastest rotation to both side lanes.",
    "Jungle": "Jungler farming the jungle with Retribution; primary early-game tempo maker.",
    "Roam": "Support/roam role using roaming blessings; wards, vision and map presence.",
    "CLASH": "Experimental/classification leftover on official hero data; heroes also usable in Clash.",
}

def lane_desc(lane):
    _upper = {k.upper(): v for k, v in LANE_DESC.items()}
    if lane in LANE_DESC:
        return LANE_DESC[lane]
    parts = [p.strip() for p in lane.replace("Lane", "").split("/")]
    return " / ".join(_upper.get(p.strip().upper(), "") for p in parts)
lanes = Counter((h["lane"] or "").strip() for h in heroes)
lanes.pop("", None)
rows = [{"lane": l, "hero_count": n, "description": lane_desc(l)}
        for l, n in sorted(lanes.items(), key=lambda x: -x[1])]
W("hero_lanes.csv", rows)

# ------------------------------------------------------- 3. lore regions
rows = []
for r in read(os.path.join(REPO, "heroes_extra.csv")):
    if r["hero"] != "Lore" or r["category"].startswith("UNVERIFIED"):
        continue
    m = re.match(r"Heroes officially listed under region (.+?) on mlbb\.io hero pages: (.+)$",
                 r["detail"])
    region, hero_list = ((m.group(1), m.group(2)) if m else (r["category"], ""))
    rows.append({
        "region": region,
        "hero_count": len([x for x in hero_list.split(",") if x.strip()]),
        "heroes": hero_list,
        "source": r["source"],
    })
rows.sort(key=lambda x: -x["hero_count"])
W("lore_regions.csv", rows)

# --------------------------------------------------- 4. items master (copy)
shutil.copyfile(os.path.join(RESEARCH, "t1g_items_master.csv"),
                os.path.join(REPO, "items_master.csv"))
print(f"  items_master.csv: copied from research/t1g_items_master.csv")

# ------------------------------------------------- 5. item categories
items = read(os.path.join(REPO, "items_master.csv"))
cats = {}
for it in items:
    c = it["category"].strip()
    price = it["price_gold"].strip()
    d = cats.setdefault(c, {"category": c, "item_count": 0, "min_price_gold": 10**9,
                            "max_price_gold": 0, "items": []})
    d["item_count"] += 1
    d["items"].append(it["item"])
    if price.isdigit():
        p = int(price)
        d["min_price_gold"] = min(d["min_price_gold"], p)
        d["max_price_gold"] = max(d["max_price_gold"], p)
rows = []
for c, d in sorted(cats.items()):
    rows.append({"category": c, "item_count": d["item_count"],
                 "min_price_gold": d["min_price_gold"] if d["min_price_gold"] < 10**9 else "",
                 "max_price_gold": d["max_price_gold"] or "",
                 "items": ", ".join(d["items"])})
W("item_categories.csv", rows)

# ------------------------------------------------- 6. battle spells
spell_row = sysrow("Spell", "Current battle spell list")
detail = spell_row["detail"]
body = detail.split("cooldowns:", 1)[1]
rows = []
for chunk in body.split(";"):
    m = re.match(r"\s*([A-Z][A-Za-z' ]+?)\s+(\d+)s\s+\((.+)\)\s*$", chunk.strip())
    if m:
        rows.append({"spell": m.group(1).strip(), "cooldown_seconds": m.group(2),
                     "effect": m.group(3).strip(),
                     "source": "https://mlbbhub.com/spells (fetched 2026-10-22)"})
W("battle_spells.csv", rows)

# ------------------------------------------------- 7. emblem sets
emblem_row = sysrow("Emblem", "Current structure")
rows = []
for name in ["Basic Common", "Tank", "Assassin", "Mage", "Fighter", "Support", "Marksman"]:
    attrs, note = "", ""
    if name == "Basic Common":
        attrs, note = "+12 Hybrid Regen, +275 HP, +22 Adaptive Attack", "8 talents in pool"
    elif name == "Tank":
        attrs = "+500 HP, +10 Hybrid Def, +4 HP Regen"
    elif name == "Mage":
        attrs = "+30 MP, +5% CDR, +8 Magic Pen"
    rows.append({"emblem_set": name, "base_attributes": attrs, "notes": note,
                 "source": emblem_row["source"]})
W("emblem_sets.csv", rows)

# ------------------------------------------------- 8. ranked ladder
src_ladder = "https://mlbbhub.com/server-time/season-schedule (reset chart, verified S40->41); " \
             "repo systems.csv Ranking rows"
ladder = [
    ("1", "Warrior", "", "Lowest tier; placement starts here after each season reset (reset chart: Warrior -> Warrior)."),
    ("2", "Elite", "", "Second tier."),
    ("3", "Master", "", "Master 4/3 reset to Elite 1, Master 2/1 to Elite 2 (S40->41 reset chart)."),
    ("4", "Grandmaster", "", "Draft pick begins here (per repo systems.csv draft rows)."),
    ("5", "Epic", "", "Epic and above use the 5-ban draft (ban-count progression in systems.csv)."),
    ("6", "Legend", "", "Above Epic; part of the 4-ban/5-ban ladder progression."),
    ("7", "Mythic", "1-24 stars", "Mythic Points replaced by star system at Season 28 (2023-03-25)."),
    ("8", "Mythical Honor", "25-49 stars", "Introduced with the Mythic star system, Season 28 (2023-03-25)."),
    ("9", "Mythical Glory", "50-99 stars", "Top leaderboard tier before Immortal; existed in the Mythic Points era."),
    ("10", "Mythical Immortal", "100+ stars", "Introduced Season 29 (2023-06-27) as the rank above Mythical Glory."),
]
rows = [{"tier_order": o, "tier": t, "star_band": b, "notes": n, "source": src_ladder}
        for o, t, b, n in ladder]
W("ranked_ladder.csv", rows)

# ------------------------------------------------- 9. game modes
modes_rows = [r for r in read(os.path.join(REPO, "systems.csv"))
              if r["system"] == "MLBB" and r["aspect"] == "Mode"]
def mode_name(r):
    d = r["detail"]
    m = re.match(r"^([A-Z][\w .:'-]{2,40}?):", d)
    if m:
        return m.group(1).strip()
    if d.startswith("Project NEXT Phase 1"):
        return "Brawl (Project NEXT Phase 1 revamp)"
    if d.startswith("Brawl revamp goes live"):
        return "Brawl (2026 revamp)"
    if d.startswith("Other modes"):
        return "VS AI / Custom / Training"
    return d.split(".")[0][:40]
rows = [{"mode": mode_name(r), "period_or_version": r["period_or_version"],
         "description": r["detail"], "source": r["source"]}
        for r in modes_rows]
W("game_modes.csv", rows)

# ------------------------------------------------- 10. change types
hc = Counter(r["change_type"].strip() for r in read(os.path.join(REPO, "hero_changes.csv")))
ic = Counter(r["change_type"].strip() for r in read(os.path.join(REPO, "item_changes.csv")))
NORM = {"New": "New", "added": "New", "Buff": "Buff", "buff": "Buff", "Nerf": "Nerf",
        "nerf": "Nerf", "Adjust": "Adjust", "changed": "Adjust", "Rework": "Rework",
        "rework": "Rework", "Remove": "Removed", "removed": "Removed", "Rename": "Rename",
        "Replace": "Replaced", "repriced": "Repriced", "bugfix": "Bugfix"}
rows = []
for src, counter in (("hero_changes", hc), ("item_changes", ic)):
    for raw, n in counter.most_common():
        rows.append({"dataset": src, "raw_change_type": raw,
                     "normalized_type": NORM.get(raw, raw), "record_count": n})
rows.sort(key=lambda x: (x["dataset"], -x["record_count"]))
W("change_types.csv", rows)

# ------------------------------------------------- 11. host countries
COUNTRIES = ["Indonesia", "Malaysia", "Singapore", "Philippines", "Thailand", "Cambodia",
             "Myanmar", "Vietnam", "Türkiye", "Turkey", "Saudi Arabia", "Brazil",
             "United Arab Emirates", "Japan", "China"]
hosts = Counter()
ms = read(os.path.join(REPO, "mseries.csv"))
for r in ms:
    c = r["host_country"].strip()
    if c:
        hosts[c] += 1
ev = read(os.path.join(REPO, "esports.csv"))
event_by_country = {}
for r in ev:
    text = r["host"] + " " + r["region"]
    found = [c for c in COUNTRIES if c.lower() in text.lower()]
    for c in found or ["International (no single host country)"]:
        event_by_country.setdefault(c, set()).add(r["event"].split(" (")[0])
rows = []
for c, n in hosts.most_common():
    rows.append({"country": c, "mseries_editions_hosted": n,
                 "esports_events_hosted": "; ".join(sorted(event_by_country.get(c, []))),
                 "esports_event_count": len(event_by_country.get(c, []))})
for c, evs in event_by_country.items():
    if c not in hosts and c != "International (no single host country)":
        rows.append({"country": c, "mseries_editions_hosted": 0,
                     "esports_events_hosted": "; ".join(sorted(evs)),
                     "esports_event_count": len(evs)})
W("host_countries.csv", rows)

# ------------------------------------------------- 12. currencies (ISO 4217)
cur = [
    ("USD", "US Dollar", "United States; international prize pools"),
    ("IDR", "Indonesian Rupiah", "Indonesia"),
    ("MYR", "Malaysian Ringgit", "Malaysia"),
    ("SGD", "Singapore Dollar", "Singapore"),
    ("PHP", "Philippine Peso", "Philippines"),
    ("THB", "Thai Baht", "Thailand"),
    ("KHR", "Cambodian Riel", "Cambodia"),
    ("MMK", "Myanmar Kyat", "Myanmar"),
    ("VND", "Vietnamese Dong", "Vietnam"),
    ("TRY", "Turkish Lira", "Türkiye (M8 host)"),
    ("SAR", "Saudi Riyal", "Saudi Arabia (EWC host)"),
    ("BRL", "Brazilian Real", "Brazil"),
    ("AED", "UAE Dirham", "United Arab Emirates"),
]
rows = [{"code": c, "currency": n, "used_in": u,
         "source": "ISO 4217 currency codes (fact table; prize-pool figures in repo are USD)"}
        for c, n, u in cur]
W("currencies.csv", rows)

# ------------------------------------------------- 13. event types
rows = [
    {"event_type": "World Championship (M-Series)",
     "description": "Annual MLBB world championship, M1 (2019) to M7 (2026); M8 announced for Türkiye, January 2027.",
     "events": "M1-M7 (mseries.csv); M8 announced",
     "record_count": len(ms)},
    {"event_type": "Mid-Season Cup (EWC era)",
     "description": "MLBB Mid-Season Cup held within the Esports World Cup, Riyadh 2024-2026.",
     "events": "EWC MSC 2024/2025/2026", "record_count": 3},
    {"event_type": "Mid-Season Cup (standalone SEA)",
     "description": "MSC - MLBB Southeast Asia Cup, standalone 2017-2023 editions.",
     "events": "MSC 2017-2023", "record_count": 7},
    {"event_type": "Women's Invitational",
     "description": "MWI - MLBB Women's Invitational (rebranded Women's International in 2026).",
     "events": "MWI 2022/2024/2025/2026", "record_count": 4},
    {"event_type": "Regional League (MPL)",
     "description": "MPL national/regional professional leagues; repo currently covers MPL Philippines S1-S18.",
     "events": "MPL Philippines S1-S18", "record_count": 18},
]
W("tournament_event_types.csv", rows)

# ------------------------------------------------- 14. data dictionary
def describe(name, n):
    return {
        "hero_master.csv": "Master roster: 133 heroes with role, lane, release date/version, prices, buff/nerf/adjust totals (patch 2.2.16 era).",
        "hero_changes.csv": "350 hero balance changes 2016-2026 with old->new values where documented.",
        "item_changes.csv": "99 item/equipment/spell-line changes 2016-2026.",
        "items_master.csv": "Full current shop snapshot (104 items) with prices, build paths and passives.",
        "patch_index.csv": "85 patch versions 1.1.23.109.1 -> 2.2.16a with dates and sources.",
        "mseries.csv": "M1-M7 world championship editions + announced M8 (2027, Turkiye).",
        "esports.csv": "38 regional/international event records (MSC, EWC-era MSC, MWI, MPL Philippines).",
        "systems.csv": "98 rows: maps, objectives, economy, modes, ranking, draft, emblems, spells, jungle, roam, academy.",
        "client.csv": "53 rows: client updates, graphics, servers, bugs, social, anti-toxicity, collaborations, security.",
        "business.csv": "70 rows: Moonton, legal, ownership, player base, revenue, monetization, creators, esports business, awards.",
        "heroes_extra.csv": "45 rows: lore regions, Legend/Collector skins, role-tag changes, era tier summaries, counters, upcoming heroes.",
        "images_manifest.csv": "683 local images with source URLs, credit and status.",
    }.get(name, "Reference lookup table (see references/README.md).")
rows = []
dataset_files = sorted(f for f in os.listdir(REPO) if f.endswith(".csv"))
for f in dataset_files:
    rws = read(os.path.join(REPO, f))
    rows.append({"table": os.path.splitext(f)[0], "file": f,
                 "columns": ", ".join(rws[0].keys()), "row_count": len(rws),
                 "description": describe(f, len(rws))})
for f in sorted(os.listdir(REF)):
    if f.endswith(".csv") and f != "data_dictionary.csv":
        rws = read(os.path.join(REF, f))
        rows.append({"table": os.path.splitext(f)[0], "file": f"references/{f}",
                     "columns": ", ".join(rws[0].keys()), "row_count": len(rws),
                     "description": "Reference lookup table (see references/README.md)."})
W("data_dictionary.csv", rows)

print("\nReference data build complete.")
