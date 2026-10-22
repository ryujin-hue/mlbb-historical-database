# MLBB Academy — Official In-Game Education, 2016–2026

![Project NEXT tutorial art](images/objective/onees_project_next.jpg)

## What the Academy Is

The Academy is MLBB's official in-game education layer: per-hero guide pages, recommended equipment builds, emblem suggestions, battle-spell recommendations, and tips — presented to players in the hero detail screens and the dedicated guide hub. Its purpose is to shorten the path from "installed the game" to "competent draft pick," and it is the reason MLBB's recommended builds function as a de-facto balance communication channel: when Moonton changes an item or emblem, the Academy's recommended loadouts change with it, quietly retuning millions of players' defaults without a patch-note read. For this database, Academy-recommended structures also serve as the canonical answer to scope item 16 (recommended builds, emblem sets and spells per hero), and the full current item/emblem/spell catalogues these recommendations draw from are in `items_master` (104 items) and the Emblem/Spell rows of `systems.csv`.

## Evolution Across the Decade

The Academy's history tracks the client's. In the 2016–2019 era, guidance was minimal: static recommended builds per hero and the original emblem pages, with learning happening mostly through community content. The modern shape arrived with **MLBB 2.0 (2019-07-18)** and, decisively, the **Project NEXT phases (2020-09-22, 2021-06-15, 2021-09-21)**, which rebuilt the tutorial flow, standardized hero guide presentation, and tied the recommended-build system to the post-1.5.88 equipment reality (roaming footwear + blessings, Retribution upgrades). After the **emblem revamp went live in 1.7.44 (2022-12-20)**, Academy recommendations became emblem-aware — heroes now ship with role-set + talent suggestions, not just items — and the post-revamp era added formalized "Advanced Guides" for new releases.

The clearest recent evidence of the Academy's promotional role is the **Zetian launch (June 2025)**: Moonton ran a "GET NEW HERO ZETIAN FOR FREE" event alongside an official **Zetian Advanced Guide** and an Academy Guide Creation Event (official announcement 2025-06-21), making the Academy a launch-stage marketing surface, not just a help section. The current 2.2.16-era client (2026) continues this: mode-unlock guidance is embedded in the Academy/mode flows (VS A.I. and Custom at Elite, Magic Chess at account level 12, 1 VS 1 at level 25 per the official patch notes), and the **Multiplayer Training Camp** added in 2.2.16 (2026-09-16) extends the education layer into interactive practice. Client-side additions like post-match **Highlights and Match Replays (2.1.88, 2026-06-17)** complement the Academy by letting players study their own games — the self-service end of the same teaching pipeline.

## What the Academy Contains Today (patch 2.2.16 era)

- **Hero guides**: one page per hero (133 as of October 2026) with kit explanation, recommended items, emblem set + talents, and battle spell.
- **Recommended builds**: default item paths mirroring `items_master.csv` (e.g. attack/magic/defense/movement lines, roam and jungle blessing items) that update with balance patches.
- **Emblem guidance**: the 7-set structure (Basic Common, Tank, Assassin, Mage, Fighter, Support, Marksman) with Standard (16) and Core (8) talent pools, pick-3 loadouts.
- **Spell guidance**: the 12-spell current catalogue with cooldowns (Retribution 35s through Flicker 120s), matched to hero kits.
- **Advanced Guides**: deep-dive official guides for new/complex heroes (Zetian, June 2025) and system changes.
- **Practice surfaces**: Multiplayer Training Camp (2.2.16), VS A.I., Custom rooms, and the mode-unlock progression noted above.

## How This Database Represents Academy Data

Academy-related rows live in `systems.csv` (`system=Academy`), build/price ground truth in `items_master.csv`, spell/emblem catalogues in the Emblem/Spell rows of `systems.csv`, and per-hero recommendations are reflected in `hero_master.csv` role/lane tags (which follow the official hero data the Academy displays). Gaps are flagged honestly: the Project NEXT tutorial-era specifics and the exact 2016–2019 Academy screen history are `UNVERIFIED` (the old client pages are not archived anywhere reachable), and per-hero recommended-build snapshots across historical patches were not captured — only the current-era structure is fully documented.
