# Reference Data (lookup tables)

Derived lookup tables feeding `/api/v1/reference/*` and `/api/v1/systems/*` endpoints.
Every row is derived from the repo's verified datasets — no fabricated values; unknown
attributes stay empty. Regenerate with `python3 scripts/build_reference_data.py`.

| Table | Rows | Contents |
|-------|------|----------|
| hero_roles.csv | 24 | Hero roles (incl. multi-role tags like fighter/assassin) + counts |
| hero_lanes.csv | 14 | Lane assignments (Gold/EXP/Mid/Jungle/Roam + combos) + counts |
| lore_regions.csv | 14 | In-game lore regions from official mlbb.io hero pages |
| item_categories.csv | 16 | Item shop categories with counts and price ranges |
| battle_spells.csv | 12 | Current 12 battle spells with cooldowns and effects |
| emblem_sets.csv | 7 | Post-1.7.44 emblem sets; base attributes where documented |
| ranked_ladder.csv | 10 | Warrior → Mythical Immortal ladder with star bands |
| game_modes.csv | 17 | All game modes with launch periods and status |
| change_types.csv | 21 | Change-type taxonomy (raw + normalized) with record counts |
| host_countries.csv | 7 | M-Series/esports host countries with event counts |
| currencies.csv | 13 | ISO 4217 currencies for host/esports markets (prize pools are USD) |
| tournament_event_types.csv | 5 | Event-type taxonomy (M-Series, MSC/EWC, MWI, MPL) |
| data_dictionary.csv | 24 | Column-level data dictionary for every table in the repo |
