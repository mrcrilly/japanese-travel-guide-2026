from __future__ import annotations

import json
import shutil
from pathlib import Path

try:
    from jinja2 import Environment, FileSystemLoader, select_autoescape
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "Jinja2 is required. Install it with `python3 -m pip install -r requirements.txt` "
        "or run this script with a Python environment that already has Jinja2."
    ) from exc


ROOT = Path(__file__).parent
TEMPLATES_DIR = ROOT / "templates"
ASSETS_DIR = ROOT / "assets"
DATA_DIR = ROOT / "data"
OUT_DIR = ROOT / "out"
DOCS_DIR = ROOT / "docs"
FINANCIAL_CACHE_FILE = DATA_DIR / "financial_cache.json"


def load_financial_cache() -> dict:
    return json.loads(FINANCIAL_CACHE_FILE.read_text(encoding="utf-8"))


FINANCIAL_CACHE = load_financial_cache()
FX_DATE = FINANCIAL_CACHE["fx"]["aud_jpy_date"]
AUD_JPY_CLOSE = FINANCIAL_CACHE["fx"]["aud_jpy_close"]
JPY_TO_AUD = 1 / AUD_JPY_CLOSE
SGD_AUD_FX_DATE = FINANCIAL_CACHE["fx"]["sgd_aud_date"]
SGD_TO_AUD = FINANCIAL_CACHE["fx"]["sgd_to_aud"]


def is_range(value: object) -> bool:
    return isinstance(value, (tuple, list))


def cost_bounds(value: int | float | tuple[int | float, int | float] | list[int | float]) -> tuple[float, float]:
    if is_range(value):
        return float(value[0]), float(value[1])  # type: ignore[index]
    return float(value), float(value)


def scale_cost(value: int | float | tuple[int | float, int | float] | list[int | float], factor: int | float) -> int | float | tuple[float, float]:
    low, high = cost_bounds(value)
    if low == high:
        return low * factor
    return low * factor, high * factor


def add_costs(*values: int | float | tuple[int | float, int | float] | list[int | float]) -> int | float | tuple[float, float]:
    total_low = 0.0
    total_high = 0.0
    for value in values:
        low, high = cost_bounds(value)
        total_low += low
        total_high += high
    if total_low == total_high:
        return total_low
    return total_low, total_high


def yen(value: int | tuple[int, int] | list[int]) -> str:
    if is_range(value):
        return f"JPY {value[0]:,}-{value[1]:,}"
    return f"JPY {value:,}"


def aud(value: int | tuple[int, int] | list[int]) -> str:
    if is_range(value):
        return f"AUD {value[0] * JPY_TO_AUD:,.2f}-{value[1] * JPY_TO_AUD:,.2f}"
    return f"AUD {value * JPY_TO_AUD:,.2f}"


def money(value: int | tuple[int, int] | list[int]) -> str:
    return f"{yen(value)} / {aud(value)}"


def aud_amount(value: int | float | tuple[int | float, int | float] | list[int | float]) -> str:
    if is_range(value):
        return f"AUD {value[0]:,.0f}-{value[1]:,.0f}"
    return f"AUD {value:,.0f}"


def sgd_to_aud_value(value: int | float | tuple[int | float, int | float] | list[int | float]) -> int | float | tuple[float, float]:
    return scale_cost(value, SGD_TO_AUD)


def sgd_to_aud(value: int | float | tuple[int | float, int | float] | list[int | float]) -> str:
    return aud_amount(sgd_to_aud_value(value))


def vocab_item(japanese: str, romaji: str, meaning: str) -> dict[str, str]:
    return {"japanese": japanese, "romaji": romaji, "meaning": meaning}


def phrase_line(japanese: str, romaji: str, english: str) -> dict[str, str]:
    return {"japanese": japanese, "romaji": romaji, "english": english}


def family_cost(value: int | tuple[int, int] | list[int] | float | tuple[float, float] | list[float], family_size: int = 4) -> int | float | tuple[float, float]:
    if is_range(value):
        return value[0] * family_size, value[1] * family_size
    return value * family_size


def build_google_maps_direction(points: list[str]) -> str:
    if len(points) < 2:
        return "https://www.google.com/maps"
    origin = points[0]
    destination = points[-1]
    waypoints = "/".join(points[1:-1])
    if waypoints:
        return f"https://www.google.com/maps/dir/{origin}/{waypoints}/{destination}"
    return f"https://www.google.com/maps/dir/{origin}/{destination}"


def citation_index(citations: list[dict]) -> dict[str, dict]:
    return {citation["id"]: citation for citation in citations}


def build_data() -> dict:
    citations = [
        {
            "id": "S01",
            "title": "smartEX ordinary car reserved-seat price table",
            "publisher": "smartEX",
            "url": "https://smart-ex.jp/en/product/plan/service/pdf/service-reserve_price.pdf",
            "accessed": "2026-03-18",
            "note": "Operator PDF used for Tokaido/Sanyo Shinkansen planning fares. PDF revision shown on page: Sep 30, 2023.",
        },
        {
            "id": "S02",
            "title": "Asakusa",
            "publisher": "GO TOKYO",
            "url": "https://www.gotokyo.org/en/destinations/eastern-tokyo/asakusa/index.html",
            "accessed": "2026-03-18",
            "note": "Official Tokyo tourism overview for the Asakusa area.",
        },
        {
            "id": "S03",
            "title": "NIKKO PASS ALL AREA",
            "publisher": "Tobu Railway",
            "url": "https://www.tobu.co.jp/en/ticket/nikko/all.html",
            "accessed": "2026-03-18",
            "note": "Official Nikko sightseeing pass. Limited express surcharge is extra if you choose the faster train.",
        },
        {
            "id": "S04",
            "title": "Hakone Freepass",
            "publisher": "Odakyu Railway",
            "url": "https://www.odakyu.jp/english/feature/27880/",
            "accessed": "2026-03-18",
            "note": "Official Hakone Freepass sample prices from Shinjuku.",
        },
        {
            "id": "S05",
            "title": "Official Osaka Travel Guide",
            "publisher": "Osaka Convention & Tourism Bureau",
            "url": "https://osaka-info.jp/en/",
            "accessed": "2026-03-18",
            "note": "Official Osaka tourism site used for city highlights and itinerary framing.",
        },
        {
            "id": "S06",
            "title": "KINTETSU RAIL PASS",
            "publisher": "Kintetsu Railway",
            "url": "https://www.kintetsu.co.jp/foreign/english/",
            "accessed": "2026-03-18",
            "note": "Official pass prices for Kyoto/Nara day-trip planning from Osaka.",
        },
        {
            "id": "S07",
            "title": "Kyoto City Official Travel Guide",
            "publisher": "Kyoto City Tourism Association",
            "url": "https://kyoto.travel/en",
            "accessed": "2026-03-18",
            "note": "Official Kyoto tourism guidance.",
        },
        {
            "id": "S08",
            "title": "Nara Travel Guide",
            "publisher": "Nara City Tourism Association",
            "url": "https://narashikanko.or.jp/en/",
            "accessed": "2026-03-18",
            "note": "Official Nara tourism guidance.",
        },
        {
            "id": "S09",
            "title": "Hiroshima",
            "publisher": "Japan National Tourism Organization",
            "url": "https://www.japan.travel/en/destinations/chugoku/hiroshima/",
            "accessed": "2026-03-18",
            "note": "Official destination guide for Hiroshima city and prefecture.",
        },
        {
            "id": "S10",
            "title": "Miyajima Ferry route and fares",
            "publisher": "JR West Miyajima Ferry",
            "url": "https://jr-miyajimaferry.co.jp/en/route/",
            "accessed": "2026-03-18",
            "note": "Official ferry fare table used for Miyajima planning.",
        },
        {
            "id": "S11",
            "title": "Kanazawa travel FAQ",
            "publisher": "Kanazawa City Tourism Association",
            "url": "https://www.kanazawa-kankoukyoukai.or.jp/faq/index.html",
            "accessed": "2026-03-18",
            "note": "Official FAQ noting Kanazawa's compact sightseeing core and local transit pass pricing.",
        },
        {
            "id": "S12",
            "title": "Takayama-Shirakawa-go-Kanazawa bus fares",
            "publisher": "Nohi Bus",
            "url": "https://www.nouhibus.co.jp/highwaybus/kanazawa/",
            "accessed": "2026-03-18",
            "note": "Official bus fare table for Kanazawa, Shirakawa-go, and Takayama.",
        },
        {
            "id": "S13",
            "title": "Tourist Information Office",
            "publisher": "HIDA TAKAYAMA",
            "url": "https://www.hida.jp/english/traveltips/practicalguide/4000111.html",
            "accessed": "2026-03-18",
            "note": "Official Takayama tourism resource.",
        },
        {
            "id": "S14",
            "title": "Getting Around the Hida Region",
            "publisher": "Hida City",
            "url": "https://hida.travel/guide/getting-around/5",
            "accessed": "2026-03-18",
            "note": "Official Hida City access guide for Takayama and Hida Furukawa.",
        },
        {
            "id": "S15",
            "title": "Takayama to Hida-Furukawa",
            "publisher": "Rome2Rio",
            "url": "https://www.rome2rio.com/s/Takayama/Hida-Furukawa",
            "accessed": "2026-03-18",
            "note": "Used only for quick point-to-point fare estimation where an operator fare table was not easy to extract.",
        },
        {
            "id": "S16",
            "title": "Go! Nagano Official Travel Guide",
            "publisher": "Nagano Prefecture Tourism",
            "url": "https://www.go-nagano.net/en/",
            "accessed": "2026-03-18",
            "note": "Official Nagano tourism guidance for Zenkoji, transport, and regional trip ideas.",
        },
        {
            "id": "S17",
            "title": "Snow Monkey 1-Day Pass",
            "publisher": "Go! Nagano",
            "url": "https://db.go-nagano.net/en/travel-guide/transportation/passes/",
            "accessed": "2026-03-18",
            "note": "Official pass and transport guidance. Page also points to the new express-bus option.",
        },
        {
            "id": "S18",
            "title": "Snow Monkey Pass 2026",
            "publisher": "Snow Monkey Resorts",
            "url": "https://www.snowmonkeyresorts.com/access/snow-monkey-1-day-pass/",
            "accessed": "2026-03-18",
            "note": "Current 2026 guidance stating the pass is not available during October and November.",
        },
        {
            "id": "S19",
            "title": "Access",
            "publisher": "Visit Matsumoto",
            "url": "https://visitmatsumoto.com/en/access/",
            "accessed": "2026-03-18",
            "note": "Used for Matsumoto connections to Nagano and Takayama.",
        },
        {
            "id": "S20",
            "title": "Guide to Traveling Japan on a Budget",
            "publisher": "Japan National Tourism Organization",
            "url": "https://www.japan.travel/en/guide/japan-on-a-budget/",
            "accessed": "2026-03-18",
            "note": "Official nationwide dining budget anchor used to estimate per-person meal bands.",
        },
        {
            "id": "S21",
            "title": "Hiroshima to Kanazawa",
            "publisher": "Rome2Rio",
            "url": "https://www.rome2rio.com/s/Hiroshima-State/Kanazawa",
            "accessed": "2026-03-18",
            "note": "Used for Hiroshima to Kanazawa point-to-point planning because the route spans multiple operators after the Hokuriku extension.",
        },
        {
            "id": "S22",
            "title": "Tokyo to Osaka",
            "publisher": "Rome2Rio",
            "url": "https://www.rome2rio.com/s/Tokyo/%C5%8Csaka-Station",
            "accessed": "2026-03-18",
            "note": "Used as a secondary sanity check against operator fares.",
        },
        {
            "id": "S23",
            "title": "AUD/JPY historical data",
            "publisher": "Investing.com",
            "url": "https://www.investing.com/currencies/aud-jpy-historical-data",
            "accessed": "2026-03-18",
            "note": f"FX basis for AUD conversion. This guide uses the latest verified market close I could confirm in-session: AUD/JPY {AUD_JPY_CLOSE:.2f} on {FX_DATE}.",
        },
        {
            "id": "S29",
            "title": "Brisbane to Tokyo flight schedules",
            "publisher": "Wego",
            "url": "https://www.wego.vn/en/schedules/bne/tyo/flight-schedules-from-brisbane-to-tokyo",
            "accessed": "2026-03-18",
            "note": "Used for current direct-flight timing assumptions from Brisbane to Tokyo. Last update shown on page: March 2, 2026.",
        },
        {
            "id": "S30",
            "title": "Tokyo to Brisbane flight schedules",
            "publisher": "Wego",
            "url": "https://www.wego.com/schedules/tyo/bne/flight-schedules-from-tokyo-to-brisbane-903",
            "accessed": "2026-03-18",
            "note": "Used for return-flight timing assumptions from Tokyo to Brisbane.",
        },
        {
            "id": "S31",
            "title": "TRUNK(HOTEL) YOYOGI PARK",
            "publisher": "TRUNK(HOTEL)",
            "url": "https://yoyogipark.trunk-hotel.com/en/stay",
            "accessed": "2026-03-18",
            "note": "Official hotel page used for the Yoyogi/Tomigaya boutique stay recommendation.",
        },
        {
            "id": "S32",
            "title": "Yayoi Kusama Museum visitor information",
            "publisher": "Yayoi Kusama Museum",
            "url": "https://yayoikusamamuseum.jp/en/visit/information/",
            "accessed": "2026-03-18",
            "note": "Official museum hours, ticketing rules, pricing, and timed-entry details.",
        },
        {
            "id": "S33",
            "title": "Koedo Kawagoe Web",
            "publisher": "Koedo Kawagoe Tourism Association",
            "url": "https://www.koedo.or.jp/en/",
            "accessed": "2026-03-18",
            "note": "Official Kawagoe tourism site used for the Little Edo day-trip recommendation.",
        },
        {
            "id": "S34",
            "title": "Oedo antique market English",
            "publisher": "Oedo Antique Market",
            "url": "https://www.antique-market.jp/english/",
            "accessed": "2026-03-18",
            "note": "Official English page used for Oedo Antique Market venue, hours, rain policy, and current schedule guidance.",
        },
        {
            "id": "S35",
            "title": "Nippori Fabric Town official homepage",
            "publisher": "Nippori Fabric Town",
            "url": "https://www.nippori-senigai.com/en/about/",
            "accessed": "2026-03-18",
            "note": "Official district information for Nippori Fabric Town.",
        },
        {
            "id": "S36",
            "title": "Osaka Food Tour in Shinsekai",
            "publisher": "Hungry Osaka Tours",
            "url": "https://hungryosaka.com/osaka-food-tour-in-shinsekai/",
            "accessed": "2026-03-18",
            "note": "Official tour page used for the Osaka food walking tour request.",
        },
        {
            "id": "S37",
            "title": "CUPNOODLES MUSEUM OSAKA IKEDA",
            "publisher": "CUPNOODLES MUSEUM",
            "url": "https://www.cupnoodles-museum.jp/en/osaka_ikeda/",
            "accessed": "2026-03-18",
            "note": "Official Osaka Ikeda museum page used for the Cup Noodles Museum request.",
        },
        {
            "id": "S38",
            "title": "CUPNOODLES MUSEUM YOKOHAMA",
            "publisher": "CUPNOODLES MUSEUM",
            "url": "https://www.cupnoodles-museum.jp/en/yokohama/",
            "accessed": "2026-03-18",
            "note": "Official Yokohama museum page retained as the Tokyo-side alternate option.",
        },
        {
            "id": "S39",
            "title": "Yoyogi - Tokyo's outdoor space",
            "publisher": "GO TOKYO",
            "url": "https://www.gotokyo.org/en/destinations/western-tokyo/yoyogi/index.html",
            "accessed": "2026-03-18",
            "note": "Official Tokyo tourism area guide used for the Yoyogi stay recommendation.",
        },
        {
            "id": "S40",
            "title": "Oedo antique market welcome page",
            "publisher": "Oedo Antique Market",
            "url": "https://www.antique-market.jp/%E3%81%94%E3%81%82%E3%81%84%E3%81%95%E3%81%A4/",
            "accessed": "2026-03-18",
            "note": "Official Oedo page stating that the Tokyo International Forum market is held on the first and third Sunday of each month.",
        },
        {
            "id": "S41",
            "title": "Flights from Brisbane to Tokyo (BNE-TYO) on Japan Airlines",
            "publisher": "Japan Airlines",
            "url": "https://www.jal.co.jp/flights/en-au/flights-from-brisbane-to-tokyo",
            "accessed": "2026-03-18",
            "note": "Used for direct Brisbane-Tokyo economy fare estimates.",
        },
        {
            "id": "S42",
            "title": "Flights from Tokyo to Brisbane (TYO-BNE) on Japan Airlines",
            "publisher": "Japan Airlines",
            "url": "https://www.jal.co.jp/flights/en-jp/flights-from-tokyo-to-brisbane",
            "accessed": "2026-03-18",
            "note": "Used for direct Tokyo-Brisbane economy fare estimates.",
        },
        {
            "id": "S43",
            "title": "Flights from Brisbane to Singapore",
            "publisher": "Singapore Airlines",
            "url": "https://www.singaporeair.com/en-au/flights-from-brisbane-to-singapore-sg",
            "accessed": "2026-03-18",
            "note": "Used for Brisbane-Singapore economy fare estimates.",
        },
        {
            "id": "S44",
            "title": "Flights from Singapore to Tokyo",
            "publisher": "Singapore Airlines",
            "url": "https://www.singaporeair.com/en-sg/flights-from-singapore-to-tokyo",
            "accessed": "2026-03-18",
            "note": "Used for Singapore-Tokyo economy fare estimates.",
        },
        {
            "id": "S45",
            "title": "Singapore dollar to Australian dollars exchange rate history",
            "publisher": "Wise",
            "url": "https://wise.com/us/currency-converter/sgd-to-aud-rate/history",
            "accessed": "2026-03-18",
            "note": "Used to convert Singapore-dollar flight fares into AUD at the March 12, 2026 mid-market rate.",
        },
        {
            "id": "S46",
            "title": "Flight schedules from Brisbane to Singapore",
            "publisher": "Wego",
            "url": "https://www.wego.com/schedules/bne/sg/flight-schedules-from-brisbane-903-to-singapore",
            "accessed": "2026-03-18",
            "note": "Used for Brisbane-Singapore flight-time estimates.",
        },
        {
            "id": "S47",
            "title": "Flight schedules from Singapore to Tokyo",
            "publisher": "Wego",
            "url": "https://www.wego.com/schedules/sin/tyo/flight-schedules-from-singapore-to-tokyo",
            "accessed": "2026-03-18",
            "note": "Used for Singapore-Tokyo flight-time estimates.",
        },
        {
            "id": "S48",
            "title": "Polish Up Your Japanese",
            "publisher": "Japan National Tourism Organization",
            "url": "https://www.japan.travel/en/story/polish-up-your-japanese/",
            "accessed": "2026-03-18",
            "note": "Official travel-Japanese phrases used as an anchor for practical shopping and question forms in the language-practice tab.",
        },
        {
            "id": "S49",
            "title": "Traveling Mindfully",
            "publisher": "Japan National Tourism Organization",
            "url": "https://www.japan.travel/en/responsible-travel-guide/traveling-mindfully/",
            "accessed": "2026-03-18",
            "note": "Official etiquette guidance used for the language tab's courtesy notes about volume, photos, and considerate behavior.",
        },
        {
            "id": "S50",
            "title": "Cheap Flights from Brisbane (BNE) to Tokyo Narita (NRT) in 2026",
            "publisher": "Skyscanner",
            "url": "https://www.skyscanner.com.au/routes/bne/nrt/brisbane-to-tokyo-narita.html",
            "accessed": "2026-03-19",
            "note": "Used to widen the flight-price check beyond JAL and verify current direct-market examples and market floor pricing.",
        },
        {
            "id": "S51",
            "title": "Cheap Flights from Tokyo Narita (NRT) to Brisbane (BNE) in 2026",
            "publisher": "Skyscanner",
            "url": "https://www.skyscanner.com.au/routes/nrt/bne/tokyo-narita-to-brisbane.html",
            "accessed": "2026-03-19",
            "note": "Used to verify current Tokyo-origin return pricing and direct-carrier mix on the way home.",
        },
        {
            "id": "S52",
            "title": "Flights from Brisbane (BNE) to Tokyo (NRT)",
            "publisher": "Qantas",
            "url": "https://www.qantas.com/au/en/flight-deals/flights-from-brisbane-to-tokyo-narita.html/bne/nrt/economy",
            "accessed": "2026-03-19",
            "note": "Used for Qantas direct Brisbane-Narita timing and economy fare anchors.",
        },
        {
            "id": "S53",
            "title": "Flights to Tokyo (HND)",
            "publisher": "Qantas",
            "url": "https://www.qantas.com/au/en/flight-deals/flights-to-tokyo-haneda.html/hnd",
            "accessed": "2026-03-19",
            "note": "Used as a second Qantas Brisbane-Tokyo economy fare anchor when Haneda pricing is the published reference.",
        },
        {
            "id": "S54",
            "title": "Flights from Brisbane to Tokyo",
            "publisher": "Cathay Pacific",
            "url": "https://flights.cathaypacific.com/destinations/es_ES/flights-from-brisbane-to-tokyo",
            "accessed": "2026-03-19",
            "note": "Used for Cathay Pacific one-stop Brisbane-Tokyo economy fare anchors.",
        },
        {
            "id": "S55",
            "title": "Brisbane to Tokyo flights from 914 AUD",
            "publisher": "Philippine Airlines",
            "url": "https://flights.philippineairlines.com/en-au/flights-from-brisbane-to-tokyo",
            "accessed": "2026-03-19",
            "note": "Used for Philippine Airlines one-stop Brisbane-Tokyo economy fare anchors.",
        },
        {
            "id": "S56",
            "title": "Flights from Brisbane to Japan",
            "publisher": "Singapore Airlines",
            "url": "https://www.singaporeair.com/en-sg/flights-from-brisbane-to-japan",
            "accessed": "2026-03-19",
            "note": "Used for Singapore Airlines Brisbane-Tokyo economy fare anchors close to the target travel season.",
        },
    ]

    financial_cache = FINANCIAL_CACHE
    flight_cache = financial_cache["flights"]
    airline_cache = flight_cache["airlines"]
    stopover_cache = flight_cache["stopover"]
    transport_cache = financial_cache["transport"]
    food_cache = financial_cache["food"]
    activity_cache = financial_cache["activities"]

    direct_airline_ids = ("jetstar", "qantas", "jal")
    direct_round_trip_aud = (
        min(cost_bounds(airline_cache[airline_id]["round_trip_aud"])[0] for airline_id in direct_airline_ids),
        max(cost_bounds(airline_cache[airline_id]["round_trip_aud"])[1] for airline_id in direct_airline_ids),
    )
    direct_per_direction_aud = (
        min(cost_bounds(airline_cache[airline_id]["per_direction_aud"])[0] for airline_id in direct_airline_ids),
        max(cost_bounds(airline_cache[airline_id]["per_direction_aud"])[1] for airline_id in direct_airline_ids),
    )
    singapore_to_tokyo_aud = sgd_to_aud_value(stopover_cache["singapore_to_tokyo_sgd"])
    singapore_stopover_round_trip_aud = add_costs(
        stopover_cache["brisbane_to_singapore_aud"],
        singapore_to_tokyo_aud,
        stopover_cache["tokyo_to_brisbane_direct_aud"],
    )

    intercity_segments = [
        {
            "from": "Tokyo",
            "to": "Osaka",
            "mode": "Nozomi Shinkansen",
            "duration": "about 2h 30m",
            "adult_cost": transport_cache["intercity_segments"]["tokyo_osaka"],
            "family_cost": family_cost(transport_cache["intercity_segments"]["tokyo_osaka"]),
            "notes": "Reserved-seat planning fare using smartEX. This is the cleanest, fastest long jump in the trip.",
            "source_ids": ["S01", "S22"],
            "map_points": ["Tokyo Station", "Shin-Osaka Station"],
        },
        {
            "from": "Osaka",
            "to": "Hiroshima",
            "mode": "Nozomi Shinkansen",
            "duration": "about 1h 25m",
            "adult_cost": transport_cache["intercity_segments"]["osaka_hiroshima"],
            "family_cost": family_cost(transport_cache["intercity_segments"]["osaka_hiroshima"]),
            "notes": "Reserved-seat planning fare using smartEX from Shin-Osaka to Hiroshima.",
            "source_ids": ["S01"],
            "map_points": ["Shin-Osaka Station", "Hiroshima Station"],
        },
        {
            "from": "Hiroshima",
            "to": "Kanazawa",
            "mode": "Rail via Osaka/Tsuruga",
            "duration": "about 5h",
            "adult_cost": transport_cache["intercity_segments"]["hiroshima_kanazawa"],
            "family_cost": family_cost(transport_cache["intercity_segments"]["hiroshima_kanazawa"]),
            "notes": "Estimate range from online route planners because this trip spans multiple operators and seat choices. Use a mid-range budget if you want reserved seats without over-optimizing.",
            "source_ids": ["S21"],
            "map_points": ["Hiroshima Station", "Kanazawa Station"],
        },
        {
            "from": "Kanazawa",
            "to": "Takayama",
            "mode": "Direct highway bus",
            "duration": "about 3h 30m",
            "adult_cost": transport_cache["intercity_segments"]["kanazawa_takayama"],
            "family_cost": family_cost(transport_cache["intercity_segments"]["kanazawa_takayama"]),
            "notes": "Bus is usually the best fit here. It is also the cleanest way to fold Shirakawa-go into the route if you prefer a stopover instead of a separate day trip.",
            "source_ids": ["S12"],
            "map_points": ["Kanazawa Station", "Takayama Station"],
        },
        {
            "from": "Takayama",
            "to": "Nagano",
            "mode": "Bus to Matsumoto + train to Nagano",
            "duration": "about 4h 15m",
            "adult_cost": transport_cache["intercity_segments"]["takayama_nagano"],
            "family_cost": family_cost(transport_cache["intercity_segments"]["takayama_nagano"]),
            "notes": "Planning number combines Takayama to Matsumoto and Matsumoto to Nagano. This is a practical regional connection, not a single through fare.",
            "source_ids": ["S19"],
            "map_points": ["Takayama Station", "Matsumoto Station", "Nagano Station"],
        },
        {
            "from": "Nagano",
            "to": "Tokyo",
            "mode": "Hokuriku Shinkansen",
            "duration": "about 1h 30m",
            "adult_cost": transport_cache["intercity_segments"]["nagano_tokyo"],
            "family_cost": family_cost(transport_cache["intercity_segments"]["nagano_tokyo"]),
            "notes": "Planning fare based on the standard Tokyo-Nagano bullet train fare published in Matsumoto access guidance.",
            "source_ids": ["S19"],
            "map_points": ["Nagano Station", "Tokyo Station"],
        },
    ]

    day_trip_rows = [
        {
            "base": "Tokyo",
            "trip": "Nikko",
            "adult_cost": transport_cache["day_trips"]["tokyo_nikko"],
            "family_cost": family_cost(transport_cache["day_trips"]["tokyo_nikko"]),
            "notes": "NIKKO PASS All Area; limited express surcharge extra if you want a faster train.",
            "source_ids": ["S03"],
        },
        {
            "base": "Tokyo",
            "trip": "Hakone",
            "adult_cost": transport_cache["day_trips"]["tokyo_hakone"],
            "family_cost": family_cost(transport_cache["day_trips"]["tokyo_hakone"]),
            "notes": "Hakone Freepass sample price from Shinjuku. It is a 2-day pass, so treat this as a convenience ceiling rather than the cheapest possible 1-day outing.",
            "source_ids": ["S04"],
        },
        {
            "base": "Osaka",
            "trip": "Kyoto",
            "adult_cost": transport_cache["day_trips"]["osaka_kyoto"],
            "family_cost": family_cost(transport_cache["day_trips"]["osaka_kyoto"]),
            "notes": "KINTETSU RAIL PASS 1-day price. Good planning number if you want a simple rail-only sightseeing day.",
            "source_ids": ["S06", "S07"],
        },
        {
            "base": "Osaka",
            "trip": "Nara",
            "adult_cost": transport_cache["day_trips"]["osaka_nara"],
            "family_cost": family_cost(transport_cache["day_trips"]["osaka_nara"]),
            "notes": "Same KINTETSU RAIL PASS 1-day planning number; useful if you want Nara without fiddling with separate tickets.",
            "source_ids": ["S06", "S08"],
        },
        {
            "base": "Hiroshima",
            "trip": "Miyajima",
            "adult_cost": transport_cache["day_trips"]["hiroshima_miyajima"],
            "family_cost": family_cost(transport_cache["day_trips"]["hiroshima_miyajima"]),
            "notes": "Estimate for Hiroshima city to Miyajima by local rail/tram plus ferry and island visitor tax. Ferry fare itself is official.",
            "source_ids": ["S09", "S10"],
        },
        {
            "base": "Kanazawa",
            "trip": "Shirakawa-go",
            "adult_cost": transport_cache["day_trips"]["kanazawa_shirakawago"],
            "family_cost": family_cost(transport_cache["day_trips"]["kanazawa_shirakawago"]),
            "notes": "Round-trip direct bus using the official Kanazawa/Shirakawa-go fare table.",
            "source_ids": ["S12"],
        },
        {
            "base": "Takayama",
            "trip": "Hida Furukawa",
            "adult_cost": transport_cache["day_trips"]["takayama_hida_furukawa"],
            "family_cost": family_cost(transport_cache["day_trips"]["takayama_hida_furukawa"]),
            "notes": "Low-friction rail estimate for the 15-minute hop each way. If you want a bundled food-and-sake outing, local tourism packages run higher.",
            "source_ids": ["S14", "S15"],
        },
        {
            "base": "Nagano",
            "trip": "Snow Monkey Park",
            "adult_cost": transport_cache["day_trips"]["nagano_snow_monkey_park"],
            "family_cost": family_cost(transport_cache["day_trips"]["nagano_snow_monkey_park"]),
            "notes": "Late-October and November travelers should assume separate transport because current 2026 guidance says the pass is not sold in October or November.",
            "source_ids": ["S16", "S17", "S18"],
        },
    ]

    japan_time_math = {
        "assumption": "This calculation assumes a direct Brisbane-Narita outbound on Tuesday October 28, 2026 and a direct Narita-Brisbane return leaving Japan on Tuesday November 17, 2026.",
        "outbound": "Current schedule data shows direct Brisbane → Tokyo flights at about 8h 55m to 9h 10m, which still lands you in Japan on October 28 because Japan is one hour behind Brisbane.",
        "return": "Current schedule data shows direct Tokyo → Brisbane flights at about 8h 50m to 9h 05m, which typically gets you back to Brisbane on Wednesday November 18, 2026 if you fly out of Japan on the evening of November 17.",
        "nights": 20,
        "calendar_days": 21,
        "full_days": 19,
        "source_ids": ["S29", "S30"],
    }

    flight_options = [
        {
            "name": "Keep it direct",
            "pattern": "Brisbane → Tokyo direct, then Tokyo → Brisbane direct",
            "air_time": "about 8h 55m-9h 10m outbound and 8h 50m-9h 05m inbound",
            "flight_cost": aud_amount(direct_round_trip_aud),
            "family_cost": aud_amount(family_cost(direct_round_trip_aud)),
            "price_breakdown": [
                f"Jetstar direct base fare: about {aud_amount(airline_cache['jetstar']['per_direction_aud'])} pp each way, or {aud_amount(airline_cache['jetstar']['round_trip_aud'])} return",
                f"Qantas direct planning band: about {aud_amount(airline_cache['qantas']['per_direction_aud'])} pp each way, or {aud_amount(airline_cache['qantas']['round_trip_aud'])} return",
                f"Japan Airlines direct planning band: about {aud_amount(airline_cache['jal']['per_direction_aud'])} pp each way, or {aud_amount(airline_cache['jal']['round_trip_aud'])} return",
            ],
            "japan_time": "20 nights / 19 full days in Japan",
            "notes": "All headline totals in this row are estimated return fares per person unless a line explicitly says one-way or each way. Jetstar is the cheapest direct entry point if you can tolerate low-cost extras, Qantas sits in the middle, and JAL remains the higher full-service direct reference closest to your travel window.",
            "source_ids": ["S29", "S30", "S41", "S50", "S51", "S52", "S53"],
        },
        {
            "name": "Singapore stopover outbound",
            "pattern": "Brisbane → Singapore, 2 nights in Singapore, then Singapore → Tokyo; return Tokyo → Brisbane direct",
            "air_time": "about 7h 40m-8h 00m to Singapore, 6h 30m-6h 35m to Tokyo, then 8h 50m-9h 05m home",
            "flight_cost": aud_amount(singapore_stopover_round_trip_aud),
            "family_cost": aud_amount(family_cost(singapore_stopover_round_trip_aud)),
            "price_breakdown": [
                f"Brisbane → Singapore: {aud_amount(stopover_cache['brisbane_to_singapore_aud'])} pp",
                f"Singapore → Tokyo: {sgd_to_aud(stopover_cache['singapore_to_tokyo_sgd'])} pp",
                f"Tokyo → Brisbane direct: {aud_amount(stopover_cache['tokyo_to_brisbane_direct_aud'])} pp",
            ],
            "japan_time": "18 nights / 17 full days in Japan",
            "notes": f"The headline total here is an estimated return total per person for the whole stopover routing. The leg lines underneath are one-way components. Treat this as a deliberate stopover choice, not the cheapest routing. The current airline checks suggest Jetstar direct and some one-stop carriers are cheaper than constructing a Singapore stop plus a separate direct return. Brisbane-Singapore is around {aud_amount(stopover_cache['brisbane_to_singapore_aud'])} pp one-way; Singapore-Tokyo works out to about {sgd_to_aud(stopover_cache['singapore_to_tokyo_sgd'])} pp one-way using S$1 = AUD {SGD_TO_AUD:.2f}; Tokyo-Brisbane direct is roughly {aud_amount(stopover_cache['tokyo_to_brisbane_direct_aud'])} pp one-way.",
            "source_ids": ["S30", "S43", "S44", "S45", "S46", "S47", "S56"],
        },
    ]

    flight_market_rows = [
        {
            "name": "Jetstar",
            "pattern": "Direct Brisbane ↔ Tokyo Narita",
            "round_trip": aud_amount(airline_cache["jetstar"]["round_trip_aud"]),
            "outbound": aud_amount(airline_cache["jetstar"]["per_direction_aud"]),
            "return_leg": aud_amount(airline_cache["jetstar"]["per_direction_aud"]),
            "family_cost": aud_amount(family_cost(airline_cache["jetstar"]["round_trip_aud"])),
            "notes": f"Cheapest direct headline fare I could verify. Skyscanner showed direct return examples from {aud_amount(airline_cache['jetstar']['round_trip_aud'])} per person. That is a base-fare style number, so bags, seats, and meals can move the true total upward.",
            "source_ids": ["S50", "S51"],
        },
        {
            "name": "Qantas",
            "pattern": "Direct Brisbane ↔ Tokyo (Narita anchor, Haneda also published)",
            "round_trip": aud_amount(airline_cache["qantas"]["round_trip_aud"]),
            "outbound": aud_amount(airline_cache["qantas"]["per_direction_aud"]),
            "return_leg": aud_amount(airline_cache["qantas"]["per_direction_aud"]),
            "family_cost": aud_amount(family_cost(airline_cache["qantas"]["round_trip_aud"])),
            "notes": f"Current Qantas pricing I could verify was {aud_amount(cost_bounds(airline_cache['qantas']['round_trip_aud'])[0])} from Brisbane to Narita and {aud_amount(cost_bounds(airline_cache['qantas']['round_trip_aud'])[1])} from Brisbane to Haneda, both economy return fares. Use this as the middle direct benchmark.",
            "source_ids": ["S52", "S53"],
        },
        {
            "name": "Japan Airlines",
            "pattern": "Direct Brisbane ↔ Tokyo",
            "round_trip": aud_amount(airline_cache["jal"]["round_trip_aud"]),
            "outbound": aud_amount(airline_cache["jal"]["per_direction_aud"]),
            "return_leg": aud_amount(airline_cache["jal"]["per_direction_aud"]),
            "family_cost": aud_amount(family_cost(airline_cache["jal"]["round_trip_aud"])),
            "notes": f"JAL is still a clean full-service direct reference, but no longer the only direct benchmark in the guide. Current Brisbane-origin examples near your season were {aud_amount(airline_cache['jal']['round_trip_aud'])} return per person.",
            "source_ids": ["S41"],
        },
        {
            "name": "Philippine Airlines",
            "pattern": "1 stop via Manila",
            "round_trip": aud_amount(airline_cache["philippine"]["round_trip_aud"]),
            "outbound": aud_amount(airline_cache["philippine"]["per_direction_aud"]),
            "return_leg": aud_amount(airline_cache["philippine"]["per_direction_aud"]),
            "family_cost": aud_amount(family_cost(airline_cache["philippine"]["round_trip_aud"])),
            "notes": f"Best full-service one-stop cash price I found from Brisbane. The published {aud_amount(airline_cache['philippine']['round_trip_aud'])} fare was for Nov 7-23, 2026, which is close enough to your travel season to use as a planning anchor.",
            "source_ids": ["S55"],
        },
        {
            "name": "Cathay Pacific",
            "pattern": "1 stop via Hong Kong",
            "round_trip": aud_amount(airline_cache["cathay"]["round_trip_aud"]),
            "outbound": aud_amount(airline_cache["cathay"]["per_direction_aud"]),
            "return_leg": aud_amount(airline_cache["cathay"]["per_direction_aud"]),
            "family_cost": aud_amount(family_cost(airline_cache["cathay"]["round_trip_aud"])),
            "notes": "Useful one-stop middle ground if you want a stronger airline product than Jetstar without paying JAL-level direct pricing.",
            "source_ids": ["S54"],
        },
        {
            "name": "Singapore Airlines",
            "pattern": "1 stop via Singapore",
            "round_trip": aud_amount(airline_cache["singapore"]["round_trip_aud"]),
            "outbound": aud_amount(airline_cache["singapore"]["per_direction_aud"]),
            "return_leg": aud_amount(airline_cache["singapore"]["per_direction_aud"]),
            "family_cost": aud_amount(family_cost(airline_cache["singapore"]["round_trip_aud"])),
            "notes": "Singapore Airlines looks solid operationally, but on the fare pages I could verify it was not cheaper than direct Jetstar or the best one-stop alternatives from Brisbane.",
            "source_ids": ["S56"],
        },
    ]

    requested_highlights = [
        {
            "title": "Boutique stay near Yoyogi-Koen",
            "base": "Final Tokyo stay",
            "best_slot": "Nov 14-17, 2026",
            "cost": "Hotel pricing varies; book early",
            "notes": "Best-fit recommendation: TRUNK(HOTEL) YOYOGI PARK in Tomigaya. This is an inference from its boutique positioning and Yoyogi Park location, and it fits your request better than a generic Shinjuku or Ginza base.",
            "source_ids": ["S31", "S39"],
        },
        {
            "title": "Yayoi Kusama Museum",
            "base": "Final Tokyo stay",
            "best_slot": "Saturday Nov 14, 2026",
            "cost": f"{money(activity_cache['yayoi_kusama_adult_jpy'])} adult",
            "notes": "Strong fit for the final Tokyo weekend because the museum is open Thursday to Sunday and national holidays only. Tickets are timed, 90 minutes, and online-only.",
            "source_ids": ["S32"],
        },
        {
            "title": "Oedo Antique Market",
            "base": "Final Tokyo stay",
            "best_slot": "Sunday Nov 15, 2026",
            "cost": "Free entry",
            "notes": "The official Oedo pages say the Tokyo International Forum market runs on the first and third Sundays each month. That means your trip hits Sunday November 1 and Sunday November 15, 2026; November 15 is the cleaner fit because it is inside your final Tokyo block. Market is canceled if it rains.",
            "source_ids": ["S34", "S40"],
        },
        {
            "title": "Nippori Fabric Town",
            "base": "Final Tokyo stay",
            "best_slot": "Saturday Nov 14 or Monday Nov 16, 2026",
            "cost": "Shopping spend varies",
            "notes": "Very easy Tokyo shopping half-day. The official district site says the area covers about 80 shops over roughly one kilometer from Nippori Station.",
            "source_ids": ["S35"],
        },
        {
            "title": "Koedo Kawagoe day trip",
            "base": "Final Tokyo stay",
            "best_slot": "Monday Nov 16, 2026",
            "cost": "Rail cost varies by start station",
            "notes": "Best placed in the final Tokyo block. The official tourism site pitches Kawagoe as about 30 minutes from the city center, with enough retro streets, snacks, and old-town walking to fill most of a day without overcommitting.",
            "source_ids": ["S33"],
        },
        {
            "title": "Cup Noodles Museum",
            "base": "Osaka",
            "best_slot": "Nov 2 or Nov 4, 2026",
            "cost": f"Osaka Ikeda entry free; My CUPNOODLES Factory {money(activity_cache['cupnoodles_factory_jpy'])} each",
            "notes": "Osaka Ikeda is the cleaner fit than Yokohama for this route. The official site says it is about 20 minutes from Hankyu Osaka-Umeda to Ikeda Station, then about a 5-minute walk. Keep Yokohama as a backup only if you later rebalance Tokyo.",
            "source_ids": ["S37", "S38"],
        },
        {
            "title": "Hungry Osaka food walking tour",
            "base": "Osaka",
            "best_slot": "Evening on Nov 2 or Nov 3, 2026",
            "cost": f"{money(activity_cache['hungry_osaka_food_tour_jpy'])} pp",
            "notes": "This is a direct match for your food-first Osaka stop. Official tour details: 3 to 3.5 hours, 15 dishes, 3 drinks, Shinsekai focus, and meeting outside Ebisucho Station Exit 3.",
            "source_ids": ["S36"],
        },
    ]

    food_budgets = [
        {
            "location": "Tokyo",
            "per_person": food_cache["tokyo"]["per_person_jpy"],
            "family_of_four": family_cost(food_cache["tokyo"]["per_person_jpy"]),
            "day_trip_add_on": f"+{money(food_cache['tokyo']['day_trip_add_on_jpy'])} pp on Nikko/Hakone days",
            "notes": "Tokyo is the priciest base in this route, but casual food is still good value if you mix konbini breakfasts, lunch sets, and one proper dinner.",
            "source_ids": ["S20"],
        },
        {
            "location": "Osaka",
            "per_person": food_cache["osaka"]["per_person_jpy"],
            "family_of_four": family_cost(food_cache["osaka"]["per_person_jpy"]),
            "day_trip_add_on": f"+{money(food_cache['osaka']['day_trip_add_on_jpy'])} pp on Kyoto/Nara days",
            "notes": "Osaka is a strong food city with many affordable casual meals, so this is a little softer than Tokyo.",
            "source_ids": ["S20", "S05"],
        },
        {
            "location": "Hiroshima",
            "per_person": food_cache["hiroshima"]["per_person_jpy"],
            "family_of_four": family_cost(food_cache["hiroshima"]["per_person_jpy"]),
            "day_trip_add_on": f"+{money(food_cache['hiroshima']['day_trip_add_on_jpy'])} pp on Miyajima day",
            "notes": "City meals are moderate; seafood-heavy or shrine-area lunches on Miyajima push the upper end.",
            "source_ids": ["S20", "S09"],
        },
        {
            "location": "Kanazawa",
            "per_person": food_cache["kanazawa"]["per_person_jpy"],
            "family_of_four": family_cost(food_cache["kanazawa"]["per_person_jpy"]),
            "day_trip_add_on": f"+{money(food_cache['kanazawa']['day_trip_add_on_jpy'])} pp on Shirakawa-go day",
            "notes": "Seafood and market lunches can easily nudge this upward, but standard family dining still fits this band.",
            "source_ids": ["S20", "S11"],
        },
        {
            "location": "Takayama",
            "per_person": food_cache["takayama"]["per_person_jpy"],
            "family_of_four": family_cost(food_cache["takayama"]["per_person_jpy"]),
            "day_trip_add_on": f"+{money(food_cache['takayama']['day_trip_add_on_jpy'])} pp if you add sake or Hida beef tastings",
            "notes": "Takayama is compact but tourist-oriented. Hida beef snacks, sake tastings, and ryokan upgrades move this quickly.",
            "source_ids": ["S20", "S13"],
        },
        {
            "location": "Nagano",
            "per_person": food_cache["nagano"]["per_person_jpy"],
            "family_of_four": family_cost(food_cache["nagano"]["per_person_jpy"]),
            "day_trip_add_on": f"+{money(food_cache['nagano']['day_trip_add_on_jpy'])} pp on Snow Monkey day",
            "notes": "Nagano is one of the easier places in this route to keep food costs under control if you stay around Zenkoji and the station area.",
            "source_ids": ["S20", "S16"],
        },
    ]

    stays = [
        {
            "name": "Tokyo",
            "slug": "tokyo-first",
            "region": "Kanto",
            "dates": "2026-10-28 to 2026-11-01",
            "nights": 4,
            "coord": [35.681236, 139.767125],
            "summary": "Start with Tokyo for the big-city landing: temples, neon, department-store food halls, parks, and enough easy family logistics to shake off jet lag without rushing into long transfers.",
            "city_focus": [
                "Asakusa and Senso-ji for a classic first-day Tokyo feel, with a Sumida River or Tokyo Skytree add-on.",
                "Shibuya, Harajuku, and Meiji Jingu for a strong contrast between shrine calm and modern Tokyo.",
                "Ueno or Odaiba if you want museums, kid-friendly space, or a lighter second city day.",
                "Keep this first Tokyo block relatively easy. Your wife's higher-friction Tokyo requests fit more cleanly in the final Tokyo stay, when you are not fighting jet lag or a same-day Osaka transfer.",
            ],
            "day_trips": [
                {
                    "name": "Nikko",
                    "coord": [36.7199, 139.6982],
                    "transport": "Tobu Railway from Asakusa",
                    "adult_cost": transport_cache["day_trips"]["tokyo_nikko"],
                    "family_cost": family_cost(transport_cache["day_trips"]["tokyo_nikko"]),
                    "duration": "full day",
                    "notes": "Best if you want shrines, mountain scenery, and a completely different rhythm from Tokyo.",
                    "source_ids": ["S03"],
                    "map_points": ["Asakusa Station", "Tobu Nikko Station"],
                },
                {
                    "name": "Hakone",
                    "coord": [35.2323, 139.1069],
                    "transport": "Odakyu from Shinjuku",
                    "adult_cost": transport_cache["day_trips"]["tokyo_hakone"],
                    "family_cost": family_cost(transport_cache["day_trips"]["tokyo_hakone"]),
                    "duration": "long day",
                    "notes": "Good for ropeways, lake views, and a possible Mt Fuji day if the weather cooperates. The official planning fare is a 2-day pass, so this is a generous estimate for a one-day outing.",
                    "source_ids": ["S04"],
                    "map_points": ["Shinjuku Station", "Hakone-Yumoto Station"],
                },
            ],
            "food_budget": next(item for item in food_budgets if item["location"] == "Tokyo"),
            "source_ids": ["S02", "S03", "S04", "S20"],
        },
        {
            "name": "Osaka",
            "slug": "osaka",
            "region": "Kansai",
            "dates": "2026-11-01 to 2026-11-05",
            "nights": 4,
            "coord": [34.7025, 135.4959],
            "summary": "Osaka gives you a looser, food-first city base with excellent rail reach into the rest of Kansai, which makes it the strongest stop in the trip for a true 50/50 city versus day-trip split.",
            "city_focus": [
                "Dotonbori and Namba for the classic canal, signs, takoyaki, okonomiyaki, and late-day energy.",
                "Osaka Castle plus the museum/park belt if you want a history day without leaving the city.",
                "Umeda or Shinsekai for skyline, retro streets, and easy family-friendly dining.",
                "Use one Osaka evening for the Hungry Osaka Shinsekai food walking tour if you want a guided food splurge that directly matches your wife's list.",
            ],
            "day_trips": [
                {
                    "name": "Kyoto",
                    "coord": [35.0116, 135.7681],
                    "transport": "Rail from Osaka",
                    "adult_cost": transport_cache["day_trips"]["osaka_kyoto"],
                    "family_cost": family_cost(transport_cache["day_trips"]["osaka_kyoto"]),
                    "duration": "full day",
                    "notes": "Use Kyoto for temples, old lanes, and a different cultural tone. Pick one Kyoto zone rather than trying to conquer the whole city in a day.",
                    "source_ids": ["S06", "S07"],
                    "map_points": ["Osaka-Namba Station", "Kyoto Station"],
                },
                {
                    "name": "Nara",
                    "coord": [34.6851, 135.8048],
                    "transport": "Rail from Osaka",
                    "adult_cost": transport_cache["day_trips"]["osaka_nara"],
                    "family_cost": family_cost(transport_cache["day_trips"]["osaka_nara"]),
                    "duration": "easy full or half day",
                    "notes": "Best easy family excursion from Osaka: deer park, Todaiji, broad paths, and a lower-stress pace than Kyoto.",
                    "source_ids": ["S06", "S08"],
                    "map_points": ["Osaka-Namba Station", "Kintetsu-Nara Station"],
                },
            ],
            "food_budget": next(item for item in food_budgets if item["location"] == "Osaka"),
            "source_ids": ["S05", "S06", "S07", "S08", "S20"],
        },
        {
            "name": "Hiroshima",
            "slug": "hiroshima",
            "region": "Chugoku",
            "dates": "2026-11-05 to 2026-11-08",
            "nights": 3,
            "coord": [34.3977, 132.4757],
            "summary": "Three nights in Hiroshima is enough to give the city emotional weight instead of treating it as a box-tick. The city day and the Miyajima day balance each other well.",
            "city_focus": [
                "Peace Memorial Park, museum, and Atomic Bomb Dome as the essential core day.",
                "Hiroshima Castle, Shukkeien, and an okonomiyaki dinner if you want a gentler second city rhythm.",
            ],
            "day_trips": [
                {
                    "name": "Miyajima",
                    "coord": [34.2959, 132.3198],
                    "transport": "Local rail/tram plus ferry",
                    "adult_cost": transport_cache["day_trips"]["hiroshima_miyajima"],
                    "family_cost": family_cost(transport_cache["day_trips"]["hiroshima_miyajima"]),
                    "duration": "full day",
                    "notes": "The obvious out-of-city pairing: shrine, torii, ropeway views if the weather is clear, and enough food stalls to make the day fun for kids.",
                    "source_ids": ["S09", "S10"],
                    "map_points": ["Hiroshima Station", "Miyajimaguchi Pier", "Itsukushima Shrine"],
                },
            ],
            "food_budget": next(item for item in food_budgets if item["location"] == "Hiroshima"),
            "source_ids": ["S09", "S10", "S20"],
        },
        {
            "name": "Kanazawa",
            "slug": "kanazawa",
            "region": "Hokuriku",
            "dates": "2026-11-08 to 2026-11-10",
            "nights": 2,
            "coord": [36.5781, 136.6486],
            "summary": "Kanazawa is your compact culture stop: garden, castle, preserved districts, and a food market all within a manageable sightseeing core.",
            "city_focus": [
                "Kenrokuen, Kanazawa Castle, and the nearby museum district.",
                "Omicho Market and Higashi Chaya for the most atmospheric city wandering.",
            ],
            "day_trips": [
                {
                    "name": "Shirakawa-go",
                    "coord": [36.2577, 136.9062],
                    "transport": "Direct bus",
                    "adult_cost": transport_cache["day_trips"]["kanazawa_shirakawago"],
                    "family_cost": family_cost(transport_cache["day_trips"]["kanazawa_shirakawago"]),
                    "duration": "full day",
                    "notes": "Strongest out-of-city choice from Kanazawa, but it is even more efficient if you do it as a transfer stop en route to Takayama instead of a pure day trip.",
                    "source_ids": ["S12"],
                    "map_points": ["Kanazawa Station", "Shirakawa-go"],
                },
            ],
            "food_budget": next(item for item in food_budgets if item["location"] == "Kanazawa"),
            "source_ids": ["S11", "S12", "S20"],
        },
        {
            "name": "Takayama",
            "slug": "takayama",
            "region": "Hida",
            "dates": "2026-11-10 to 2026-11-12",
            "nights": 2,
            "coord": [36.1431, 137.2522],
            "summary": "Takayama changes the texture of the trip: preserved merchant streets, mountain air, Hida beef, sake, and a much slower pace than the big cities.",
            "city_focus": [
                "Sanmachi old town, morning markets, and Takayama Jinya.",
                "Hida Folk Village if the family wants a traditional-house experience without a long transfer.",
            ],
            "day_trips": [
                {
                    "name": "Hida Furukawa",
                    "coord": [36.2381, 137.1885],
                    "transport": "Short regional train hop",
                    "adult_cost": transport_cache["day_trips"]["takayama_hida_furukawa"],
                    "family_cost": family_cost(transport_cache["day_trips"]["takayama_hida_furukawa"]),
                    "duration": "half or easy full day",
                    "notes": "Best light excursion if you already saw Shirakawa-go from Kanazawa. Furukawa gives you canals, storehouses, and a quieter Hida townscape.",
                    "source_ids": ["S14", "S15"],
                    "map_points": ["Takayama Station", "Hida-Furukawa Station"],
                },
            ],
            "food_budget": next(item for item in food_budgets if item["location"] == "Takayama"),
            "source_ids": ["S13", "S14", "S15", "S20"],
        },
        {
            "name": "Nagano",
            "slug": "nagano",
            "region": "Chubu / Shinshu",
            "dates": "2026-11-12 to 2026-11-14",
            "nights": 2,
            "coord": [36.6485, 138.1942],
            "summary": "Nagano is a smart reset before the final Tokyo stretch: Zenkoji for culture, mountain food, and an easy launch point for the monkey-park side trip.",
            "city_focus": [
                "Zenkoji and the approach streets for a compact but worthwhile city day.",
                "Station-area food, sake, and a relaxed evening rather than trying to force too many separate sights.",
            ],
            "day_trips": [
                {
                    "name": "Snow Monkey Park",
                    "coord": [36.7327, 138.4621],
                    "transport": "Local train or bus from Nagano",
                    "adult_cost": transport_cache["day_trips"]["nagano_snow_monkey_park"],
                    "family_cost": family_cost(transport_cache["day_trips"]["nagano_snow_monkey_park"]),
                    "duration": "full day",
                    "notes": "As of March 2, 2026, the current Snow Monkey pass guidance says the pass is not sold in October or November, so use point-to-point transport pricing for your November 2026 dates.",
                    "source_ids": ["S16", "S17", "S18"],
                    "map_points": ["Nagano Station", "Snow Monkey Park"],
                },
            ],
            "food_budget": next(item for item in food_budgets if item["location"] == "Nagano"),
            "source_ids": ["S16", "S17", "S18", "S20"],
        },
        {
            "name": "Tokyo",
            "slug": "tokyo-final",
            "region": "Kanto",
            "dates": "2026-11-14 to 2026-11-17",
            "nights": 3,
            "coord": [35.681236, 139.767125],
            "summary": "Use the return to Tokyo as a buffer rather than cramming in another huge travel day. It is the right place for shopping, weather recovery, and anything you missed on the first landing.",
            "city_focus": [
                "Base this stay in the Yoyogi/Tomigaya pocket if you want the boutique-hotel request to shape the trip rather than feel tacked on at the end.",
                "Saturday November 14 works well for Yayoi Kusama Museum plus either Nippori Fabric Town or a Yoyogi/Tomigaya wandering day.",
                "Sunday November 15, 2026 is a strong Oedo Antique Market day because it lands cleanly inside this Tokyo stay.",
                "Monday November 16 is the best slot for the Koedo Kawagoe day trip if you want the requested Little Edo outing.",
            ],
            "day_trips": [],
            "food_budget": next(item for item in food_budgets if item["location"] == "Tokyo"),
            "source_ids": ["S02", "S20", "S31", "S32", "S33", "S34", "S35", "S39", "S40"],
        },
    ]

    for segment in intercity_segments:
        segment["adult_cost_label"] = money(segment["adult_cost"])
        segment["family_cost_label"] = money(segment["family_cost"])
        segment["maps_url"] = build_google_maps_direction(segment["map_points"])

    for row in day_trip_rows:
        row["adult_cost_label"] = money(row["adult_cost"])
        row["family_cost_label"] = money(row["family_cost"])

    for food in food_budgets:
        food["per_person_label"] = money(food["per_person"])
        food["family_of_four_label"] = money(food["family_of_four"])

    for stay in stays:
        stay["maps_url"] = build_google_maps_direction([f"{stay['name']} Station"])
        for trip in stay["day_trips"]:
            trip["adult_cost_label"] = money(trip["adult_cost"])
            trip["family_cost_label"] = money(trip["family_cost"])
            trip["maps_url"] = build_google_maps_direction(trip["map_points"])

    city_focus_days = 10
    excursion_days = 8

    mid_intercity_total = 0
    for segment in intercity_segments:
        if is_range(segment["adult_cost"]):
            mid_intercity_total += round(sum(segment["adult_cost"]) / 2)
        else:
            mid_intercity_total += segment["adult_cost"]

    route_map = [
        {"name": "Tokyo", "coord": [35.681236, 139.767125]},
        {"name": "Osaka", "coord": [34.7025, 135.4959]},
        {"name": "Hiroshima", "coord": [34.3977, 132.4757]},
        {"name": "Kanazawa", "coord": [36.5781, 136.6486]},
        {"name": "Takayama", "coord": [36.1431, 137.2522]},
        {"name": "Nagano", "coord": [36.6485, 138.1942]},
        {"name": "Tokyo", "coord": [35.681236, 139.767125]},
    ]

    day_trip_maps = [
        {
            "id": "route-overview",
            "title": "Main route",
            "points": route_map,
        }
    ]
    for stay in stays:
        points = [{"name": stay["name"], "coord": stay["coord"]}]
        for trip in stay["day_trips"]:
            points.append({"name": trip["name"], "coord": trip["coord"]})
        day_trip_maps.append(
            {
                "id": f"map-{stay['slug']}",
                "title": stay["name"],
                "points": points,
            }
        )

    dates_and_times_rows = [
        {
            "scenario": "Direct plan",
            "date_window": "Tue Oct 28, 2026",
            "place": "Brisbane → Tokyo direct flight",
            "time_detail": "about 8h 55m-9h 10m",
            "notes": "Used for the main trip math assumption. Japan remains the same calendar arrival date under this planning scenario.",
            "source_ids": ["S29"],
        },
        {
            "scenario": "Main itinerary",
            "date_window": "Oct 28-Nov 1, 2026",
            "place": "Tokyo first stay",
            "time_detail": "4 nights",
            "notes": "Landing block. Keep it lighter than the final Tokyo stay.",
            "source_ids": [],
        },
        {
            "scenario": "Main itinerary",
            "date_window": "Nov 1-Nov 5, 2026",
            "place": "Osaka stay",
            "time_detail": "4 nights",
            "notes": "Best fit for Cup Noodles Ikeda and the Hungry Osaka tour.",
            "source_ids": [],
        },
        {
            "scenario": "Requested place",
            "date_window": "Nov 2 or Nov 4, 2026",
            "place": "Cup Noodles Museum Osaka Ikeda",
            "time_detail": "9:30-16:30; last admission 15:30",
            "notes": "Closed Tuesdays. About 20 minutes from Hankyu Osaka-Umeda to Ikeda Station, then about 5 minutes on foot.",
            "source_ids": ["S37"],
        },
        {
            "scenario": "Requested place",
            "date_window": "Nov 2 or Nov 3, 2026",
            "place": "Hungry Osaka food tour",
            "time_detail": "midday or early evening; 3-3.5 hours",
            "notes": "Meeting point is outside Ebisucho Station Exit 3.",
            "source_ids": ["S36"],
        },
        {
            "scenario": "Main itinerary",
            "date_window": "Nov 5-Nov 8, 2026",
            "place": "Hiroshima stay",
            "time_detail": "3 nights",
            "notes": "City day plus Miyajima day works cleanly here.",
            "source_ids": [],
        },
        {
            "scenario": "Main itinerary",
            "date_window": "Nov 8-Nov 10, 2026",
            "place": "Kanazawa stay",
            "time_detail": "2 nights",
            "notes": "Compact stop; easiest if you keep the sightseeing core tight.",
            "source_ids": [],
        },
        {
            "scenario": "Main itinerary",
            "date_window": "Nov 10-Nov 12, 2026",
            "place": "Takayama stay",
            "time_detail": "2 nights",
            "notes": "Old-town block plus light regional side trip.",
            "source_ids": [],
        },
        {
            "scenario": "Main itinerary",
            "date_window": "Nov 12-Nov 14, 2026",
            "place": "Nagano stay",
            "time_detail": "2 nights",
            "notes": "Zenkoji plus Snow Monkey day fit here.",
            "source_ids": [],
        },
        {
            "scenario": "Main itinerary",
            "date_window": "Nov 14-Nov 17, 2026",
            "place": "Final Tokyo / Yoyogi-Tomigaya stay",
            "time_detail": "3 nights",
            "notes": "Best place to anchor the boutique-hotel request and the wife's Tokyo list.",
            "source_ids": ["S31", "S39"],
        },
        {
            "scenario": "Requested place",
            "date_window": "Sat Nov 14, 2026",
            "place": "Yayoi Kusama Museum",
            "time_detail": "11:00-17:30; timed 90-minute entry slots",
            "notes": "Open Thursdays to Sundays and national holidays only. Tickets are advance purchase only.",
            "source_ids": ["S32"],
        },
        {
            "scenario": "Requested place",
            "date_window": "Sun Nov 15, 2026",
            "place": "Oedo Antique Market",
            "time_detail": "9:00-16:00",
            "notes": "Tokyo International Forum market; canceled in rain. Your trip also touches Sunday Nov 1, but Nov 15 fits the final Tokyo stay better.",
            "source_ids": ["S34", "S40"],
        },
        {
            "scenario": "Requested place",
            "date_window": "Sat Nov 14 or Mon Nov 16, 2026",
            "place": "Nippori Fabric Town",
            "time_detail": "shop hours vary by store",
            "notes": "Best treated as a half-day shopping block rather than a fixed-ticket activity.",
            "source_ids": ["S35"],
        },
        {
            "scenario": "Requested place",
            "date_window": "Mon Nov 16, 2026",
            "place": "Koedo Kawagoe day trip",
            "time_detail": "about 30 minutes from central Tokyo; allow most of the day",
            "notes": "Best slot for the Little Edo request in the final Tokyo block.",
            "source_ids": ["S33"],
        },
        {
            "scenario": "Singapore variant",
            "date_window": "Tue Oct 28, 2026",
            "place": "Brisbane → Singapore flight",
            "time_detail": "about 7h 40m-8h 00m",
            "notes": "Outbound variant if you choose the stopover plan.",
            "source_ids": ["S46"],
        },
        {
            "scenario": "Singapore variant",
            "date_window": "Oct 28-Oct 30, 2026",
            "place": "Singapore stopover",
            "time_detail": "2 nights",
            "notes": "This variant reduces Japan time to 18 nights and 17 full sightseeing days.",
            "source_ids": [],
        },
        {
            "scenario": "Singapore variant",
            "date_window": "Thu Oct 30, 2026",
            "place": "Singapore → Tokyo flight",
            "time_detail": "about 6h 30m-6h 35m",
            "notes": "Use this if you commit to the Singapore stopover route.",
            "source_ids": ["S47"],
        },
        {
            "scenario": "Direct plan",
            "date_window": "Tue Nov 17, 2026",
            "place": "Tokyo → Brisbane direct flight",
            "time_detail": "about 8h 50m-9h 05m",
            "notes": "Planning assumption lands back in Brisbane on Wednesday Nov 18, 2026.",
            "source_ids": ["S30"],
        },
    ]

    language_core_rows = [
        {
            "topic": "Getting attention politely",
            "best_use": "Any counter, station window, or shop when you need to start a conversation without sounding abrupt.",
            "words": [
                vocab_item("すみません", "sumimasen", "excuse me / sorry / can I ask"),
                vocab_item("お願いします", "onegaishimasu", "please"),
                vocab_item("ありがとうございます", "arigatou gozaimasu", "thank you"),
            ],
            "try_line": phrase_line(
                "すみません、ちょっといいですか。",
                "Sumimasen, chotto ii desu ka.",
                "Excuse me, do you have a moment?",
            ),
            "likely_reply": phrase_line(
                "はい、どうぞ。",
                "Hai, douzo.",
                "Yes, go ahead.",
            ),
            "note": "This is the safest opener in the whole trip. Use it constantly.",
            "source_ids": ["S48", "S49"],
        },
        {
            "topic": "Asking for a recommendation",
            "best_use": "Restaurants, market stalls, bakeries, snack shops, and sake counters.",
            "words": [
                vocab_item("おすすめ", "osusume", "recommendation"),
                vocab_item("人気", "ninki", "popular"),
                vocab_item("どれ", "dore", "which one"),
            ],
            "try_line": phrase_line(
                "おすすめは何ですか。",
                "Osusume wa nan desu ka.",
                "What do you recommend?",
            ),
            "likely_reply": phrase_line(
                "こちらが人気です。",
                "Kochira ga ninki desu.",
                "This one is popular.",
            ),
            "note": "A short question like this gets you into a real exchange fast.",
            "source_ids": ["S48"],
        },
        {
            "topic": "Price, quantity, and colors",
            "best_use": "Nippori Fabric Town, markets, souvenir shops, and antiques.",
            "words": [
                vocab_item("いくら", "ikura", "how much"),
                vocab_item("ひとつ", "hitotsu", "one"),
                vocab_item("二メートル", "ni meetoru", "two meters"),
                vocab_item("色", "iro", "color"),
            ],
            "try_line": phrase_line(
                "いくらですか。ほかの色はありますか。",
                "Ikura desu ka. Hoka no iro wa arimasu ka.",
                "How much is it? Do you have another color?",
            ),
            "likely_reply": phrase_line(
                "はい、青とベージュがあります。",
                "Hai, ao to beeju ga arimasu.",
                "Yes, we have blue and beige.",
            ),
            "note": "This one is especially useful for fabric, craft, and flea-market shopping.",
            "source_ids": ["S48"],
        },
        {
            "topic": "Finding things and asking directions",
            "best_use": "Stations, museums, markets, department stores, and temple areas.",
            "words": [
                vocab_item("どこ", "doko", "where"),
                vocab_item("駅", "eki", "station"),
                vocab_item("入口", "iriguchi", "entrance"),
                vocab_item("トイレ", "toire", "toilet"),
            ],
            "try_line": phrase_line(
                "トイレはどこですか。",
                "Toire wa doko desu ka.",
                "Where is the toilet?",
            ),
            "likely_reply": phrase_line(
                "あちらです。",
                "Achira desu.",
                "It's over there.",
            ),
            "note": "Simple location questions are high-frequency and easy to say clearly.",
            "source_ids": ["S48"],
        },
        {
            "topic": "Slowing the conversation down",
            "best_use": "Any time someone answers too fast and you want to keep the exchange going instead of switching to English.",
            "words": [
                vocab_item("もう一度", "mou ichido", "one more time"),
                vocab_item("ゆっくり", "yukkuri", "slowly"),
                vocab_item("わかりました", "wakarimashita", "I understood"),
            ],
            "try_line": phrase_line(
                "すみません、もう一度ゆっくりお願いします。",
                "Sumimasen, mou ichido yukkuri onegaishimasu.",
                "Sorry, one more time slowly, please.",
            ),
            "likely_reply": phrase_line(
                "はい、わかりました。",
                "Hai, wakarimashita.",
                "Yes, understood.",
            ),
            "note": "This keeps the interaction in Japanese without pretending you caught everything.",
            "source_ids": ["S48", "S49"],
        },
    ]

    language_ideas_rows = [
        {
            "stop": "Tokyo first stay",
            "date_window": "Oct 28-Oct 31",
            "place": "Hotel check-in or bag drop around central Tokyo",
            "situation": "Use your first Japanese interaction on something predictable and low-pressure.",
            "goal": "Say your name, mention the reservation, and ask about leaving bags.",
            "words": [
                vocab_item("予約", "yoyaku", "reservation"),
                vocab_item("荷物", "nimotsu", "luggage"),
                vocab_item("先に", "saki ni", "in advance / first"),
                vocab_item("預ける", "azukeru", "to leave in someone's care"),
            ],
            "starter": phrase_line(
                "予約しています。マクリリーです。",
                "Yoyaku shite imasu. Makuririi desu.",
                "I have a reservation. My name is McReilly.",
            ),
            "likely_reply": phrase_line(
                "ありがとうございます。パスポートをお願いします。",
                "Arigatou gozaimasu. Pasupooto o onegaishimasu.",
                "Thank you. Your passports, please.",
            ),
            "your_answer": phrase_line(
                "はい、どうぞ。荷物を先に預けてもいいですか。",
                "Hai, douzo. Nimotsu o saki ni azukete mo ii desu ka.",
                "Sure. Is it okay if we leave our bags first?",
            ),
            "stretch_line": phrase_line(
                "チェックインは何時からですか。",
                "Chekkuin wa nanji kara desu ka.",
                "What time is check-in from?",
            ),
            "note": "A good first win because the staff will expect this conversation and usually speak clearly.",
            "source_ids": ["S48", "S49"],
        },
        {
            "stop": "Tokyo first stay",
            "date_window": "Oct 29-Oct 31",
            "place": "Lunch counter in Asakusa or Ueno",
            "situation": "Ask for the house favorite instead of pointing straight at the menu.",
            "goal": "Practice recommendation language and one simple follow-up question.",
            "words": [
                vocab_item("おすすめ", "osusume", "recommendation"),
                vocab_item("人気", "ninki", "popular"),
                vocab_item("ひとつ", "hitotsu", "one"),
                vocab_item("メニュー", "menyuu", "menu"),
            ],
            "starter": phrase_line(
                "おすすめは何ですか。",
                "Osusume wa nan desu ka.",
                "What do you recommend?",
            ),
            "likely_reply": phrase_line(
                "こちらの天ぷらそばが人気です。",
                "Kochira no tempura soba ga ninki desu.",
                "The tempura soba is popular.",
            ),
            "your_answer": phrase_line(
                "じゃあ、それをひとつお願いします。",
                "Jaa, sore o hitotsu onegaishimasu.",
                "Then I'll have one of those, please.",
            ),
            "stretch_line": phrase_line(
                "英語のメニューはありますか。",
                "Eigo no menyuu wa arimasu ka.",
                "Do you have an English menu?",
            ),
            "note": "Perfect for day one or two because you only need to understand one short answer.",
            "source_ids": ["S02", "S48"],
        },
        {
            "stop": "Osaka",
            "date_window": "Nov 2-Nov 4",
            "place": "Dotonbori, Shinsekai, or before the Hungry Osaka food tour",
            "situation": "Use Osaka as your food-conversation stop.",
            "goal": "Ask what is popular and react to the answer instead of just ordering silently.",
            "words": [
                vocab_item("初めて", "hajimete", "first time"),
                vocab_item("たこ焼き", "takoyaki", "octopus balls"),
                vocab_item("串カツ", "kushikatsu", "fried skewers"),
                vocab_item("あまり", "amari", "not very / not too much"),
            ],
            "starter": phrase_line(
                "初めてなんですが、おすすめは何ですか。",
                "Hajimete nan desu ga, osusume wa nan desu ka.",
                "It's my first time here, what do you recommend?",
            ),
            "likely_reply": phrase_line(
                "たこ焼きと串カツが人気です。",
                "Takoyaki to kushikatsu ga ninki desu.",
                "Takoyaki and kushikatsu are popular.",
            ),
            "your_answer": phrase_line(
                "じゃあ、たこ焼きをひとつお願いします。",
                "Jaa, takoyaki o hitotsu onegaishimasu.",
                "Then I'll have one takoyaki, please.",
            ),
            "stretch_line": phrase_line(
                "あまり辛くないですか。",
                "Amari karakunai desu ka.",
                "It's not very spicy, right?",
            ),
            "note": "Food stalls reward short, direct Japanese more than long textbook sentences.",
            "source_ids": ["S05", "S36", "S48"],
        },
        {
            "stop": "Hiroshima",
            "date_window": "Nov 5-Nov 7",
            "place": "Okonomiyaki counter",
            "situation": "Ask one question about the Hiroshima-style version and then place an order.",
            "goal": "Get comfortable with one food-specific exchange.",
            "words": [
                vocab_item("お好み焼き", "okonomiyaki", "savory pancake"),
                vocab_item("そば入り", "soba-iri", "with noodles"),
                vocab_item("牡蠣", "kaki", "oysters"),
                vocab_item("なし", "nashi", "without"),
            ],
            "starter": phrase_line(
                "広島風お好み焼きはどれですか。",
                "Hiroshima-fu okonomiyaki wa dore desu ka.",
                "Which one is the Hiroshima-style okonomiyaki?",
            ),
            "likely_reply": phrase_line(
                "こちらのそば入りです。牡蠣も入れられます。",
                "Kochira no soba-iri desu. Kaki mo ireraremasu.",
                "This one with noodles. You can add oysters too.",
            ),
            "your_answer": phrase_line(
                "じゃあ、そば入りをお願いします。牡蠣はなしで大丈夫です。",
                "Jaa, soba-iri o onegaishimasu. Kaki wa nashi de daijoubu desu.",
                "Then the one with noodles, please. No oysters is fine for us.",
            ),
            "stretch_line": phrase_line(
                "家族で分けてもいいですか。",
                "Kazoku de wakete mo ii desu ka.",
                "Is it okay if we share it as a family?",
            ),
            "note": "Counter-style places are great because you can point, listen, and repeat.",
            "source_ids": ["S09", "S48"],
        },
        {
            "stop": "Kanazawa",
            "date_window": "Nov 8-Nov 9",
            "place": "Omicho Market seafood or produce stall",
            "situation": "Ask what something is and whether it is seasonal.",
            "goal": "Build confidence asking about food you do not recognize instantly.",
            "words": [
                vocab_item("旬", "shun", "in season"),
                vocab_item("今", "ima", "now"),
                vocab_item("これ", "kore", "this"),
                vocab_item("いくら", "ikura", "how much"),
            ],
            "starter": phrase_line(
                "これは何ですか。今が旬ですか。",
                "Kore wa nan desu ka. Ima ga shun desu ka.",
                "What is this? Is it in season now?",
            ),
            "likely_reply": phrase_line(
                "のどぐろです。今の時期に人気です。",
                "Nodoguro desu. Ima no jiki ni ninki desu.",
                "It's blackthroat seaperch. It's popular this time of year.",
            ),
            "your_answer": phrase_line(
                "おいしそうですね。ひとつお願いします。",
                "Oishisou desu ne. Hitotsu onegaishimasu.",
                "That looks delicious. One, please.",
            ),
            "stretch_line": phrase_line(
                "持ち帰りできますか。",
                "Mochikaeri dekimasu ka.",
                "Can I take it away?",
            ),
            "note": "Markets are where curiosity pays off. Simple questions often get friendly answers.",
            "source_ids": ["S11", "S48"],
        },
        {
            "stop": "Takayama",
            "date_window": "Nov 10-Nov 11",
            "place": "Sake shop in the old town",
            "situation": "Ask for a tasting and compare dry versus sweeter styles.",
            "goal": "Practice preference language rather than only nouns.",
            "words": [
                vocab_item("試飲", "shiin", "tasting"),
                vocab_item("甘い", "amai", "sweet"),
                vocab_item("辛口", "karakuchi", "dry"),
                vocab_item("小さい瓶", "chiisai bin", "small bottle"),
            ],
            "starter": phrase_line(
                "少し試飲できますか。辛口が好きです。",
                "Sukoshi shiin dekimasu ka. Karakuchi ga suki desu.",
                "Can I taste a little? I like dry sake.",
            ),
            "likely_reply": phrase_line(
                "はい、こちらは辛口で、こちらは少し甘めです。",
                "Hai, kochira wa karakuchi de, kochira wa sukoshi amame desu.",
                "Yes, this one is dry, and this one is a little sweeter.",
            ),
            "your_answer": phrase_line(
                "じゃあ、辛口を少しお願いします。",
                "Jaa, karakuchi o sukoshi onegaishimasu.",
                "Then a little of the dry one, please.",
            ),
            "stretch_line": phrase_line(
                "お土産用に小さい瓶はありますか。",
                "Omiyage-you ni chiisai bin wa arimasu ka.",
                "Do you have a small bottle for a souvenir?",
            ),
            "note": "Takayama is ideal for slow, friendly practice because interactions are rarely rushed.",
            "source_ids": ["S13", "S48"],
        },
        {
            "stop": "Nagano",
            "date_window": "Nov 12-Nov 13",
            "place": "Zenkoji approach or a soba shop",
            "situation": "Ask what the local specialty is, then order it.",
            "goal": "Practice a natural one-two exchange you can reuse elsewhere.",
            "words": [
                vocab_item("名物", "meibutsu", "local specialty"),
                vocab_item("信州そば", "Shinshu soba", "Nagano soba"),
                vocab_item("温かい", "atatakai", "hot / warm"),
                vocab_item("ありますか", "arimasu ka", "do you have"),
            ],
            "starter": phrase_line(
                "このあたりの名物は何ですか。",
                "Kono atari no meibutsu wa nan desu ka.",
                "What is the local specialty around here?",
            ),
            "likely_reply": phrase_line(
                "信州そばとりんごが有名です。",
                "Shinshu soba to ringo ga yuumei desu.",
                "Shinshu soba and apples are famous.",
            ),
            "your_answer": phrase_line(
                "じゃあ、温かいそばをお願いします。",
                "Jaa, atatakai soba o onegaishimasu.",
                "Then I'd like a hot soba, please.",
            ),
            "stretch_line": phrase_line(
                "りんごジュースもありますか。",
                "Ringo juusu mo arimasu ka.",
                "Do you also have apple juice?",
            ),
            "note": "A very reusable pattern: ask the specialty, then order the specialty.",
            "source_ids": ["S16", "S48"],
        },
        {
            "stop": "Tokyo final stay",
            "date_window": "Nov 14 or Nov 16",
            "place": "Nippori Fabric Town",
            "situation": "This is one of the cleanest places in the trip for practical shopping Japanese.",
            "goal": "Ask for fabric by length and check for another color or pattern.",
            "words": [
                vocab_item("布", "nuno", "fabric"),
                vocab_item("二メートル", "ni meetoru", "two meters"),
                vocab_item("柄", "gara", "pattern"),
                vocab_item("切ってください", "kitte kudasai", "please cut it"),
            ],
            "starter": phrase_line(
                "この布を二メートルください。ほかの色はありますか。",
                "Kono nuno o ni meetoru kudasai. Hoka no iro wa arimasu ka.",
                "Please give me two meters of this fabric. Do you have another color?",
            ),
            "likely_reply": phrase_line(
                "はい、青とベージュがあります。",
                "Hai, ao to beeju ga arimasu.",
                "Yes, we have blue and beige.",
            ),
            "your_answer": phrase_line(
                "じゃあ、青を二メートルお願いします。",
                "Jaa, ao o ni meetoru onegaishimasu.",
                "Then two meters of the blue, please.",
            ),
            "stretch_line": phrase_line(
                "同じ柄で小さいサイズはありますか。",
                "Onaji gara de chiisai saizu wa arimasu ka.",
                "Do you have the same pattern in a smaller size?",
            ),
            "note": "Because you already know what you want, this is great real-world speaking practice.",
            "source_ids": ["S35", "S48"],
        },
        {
            "stop": "Tokyo final stay",
            "date_window": "Nov 15-Nov 16",
            "place": "Oedo Antique Market or Koedo Kawagoe old-town shops",
            "situation": "Ask about age, authenticity, or whether photos are okay.",
            "goal": "Have one curiosity-led exchange instead of just browsing silently.",
            "words": [
                vocab_item("骨董品", "kottouhin", "antiques"),
                vocab_item("いつごろ", "itsu goro", "around when"),
                vocab_item("本物", "honmono", "authentic / genuine"),
                vocab_item("写真", "shashin", "photo"),
            ],
            "starter": phrase_line(
                "これはいつごろのものですか。",
                "Kore wa itsu goro no mono desu ka.",
                "About when is this from?",
            ),
            "likely_reply": phrase_line(
                "昭和のものです。",
                "Shouwa no mono desu.",
                "It's from the Showa period.",
            ),
            "your_answer": phrase_line(
                "ありがとうございます。写真を撮ってもいいですか。",
                "Arigatou gozaimasu. Shashin o totte mo ii desu ka.",
                "Thank you. May I take a photo?",
            ),
            "stretch_line": phrase_line(
                "本物ですか。",
                "Honmono desu ka.",
                "Is it authentic?",
            ),
            "note": "At markets and old-town shops, ask before taking photos and keep your voice low.",
            "source_ids": ["S33", "S34", "S40", "S48", "S49"],
        },
    ]

    finance_rows = [
        {
            "category": "Flights",
            "item": "Direct Brisbane ↔ Tokyo market range",
            "per_person": aud_amount(direct_round_trip_aud),
            "family": aud_amount(family_cost(direct_round_trip_aud)),
            "details": [
                f"Jetstar direct base fare: about {aud_amount(airline_cache['jetstar']['per_direction_aud'])} each way pp",
                f"Qantas direct: about {aud_amount(airline_cache['qantas']['per_direction_aud'])} each way pp",
                f"JAL direct: about {aud_amount(airline_cache['jal']['per_direction_aud'])} each way pp",
            ],
            "notes": "This is the practical direct band after checking Skyscanner plus current Qantas and JAL fare pages. The low end is low-cost Jetstar; the high end is JAL close to your target season.",
            "source_ids": ["S41", "S50", "S51", "S52", "S53"],
        },
        {
            "category": "Flights",
            "item": "Jetstar direct Brisbane ↔ Tokyo",
            "per_person": aud_amount(airline_cache["jetstar"]["round_trip_aud"]),
            "family": aud_amount(family_cost(airline_cache["jetstar"]["round_trip_aud"])),
            "details": [
                f"Approx outbound: {aud_amount(airline_cache['jetstar']['per_direction_aud'])} pp",
                f"Approx return: {aud_amount(airline_cache['jetstar']['per_direction_aud'])} pp",
                f"Family of 4 at headline fare: {aud_amount(family_cost(airline_cache['jetstar']['round_trip_aud']))}",
            ],
            "notes": "Best cash price I could verify for direct flights. Treat it as a base fare, not an all-in family number, because luggage and seat selection can materially change the true total.",
            "source_ids": ["S50", "S51"],
        },
        {
            "category": "Flights",
            "item": "Qantas direct Brisbane ↔ Tokyo",
            "per_person": aud_amount(airline_cache["qantas"]["round_trip_aud"]),
            "family": aud_amount(family_cost(airline_cache["qantas"]["round_trip_aud"])),
            "details": [
                f"Approx outbound: {aud_amount(airline_cache['qantas']['per_direction_aud'])} pp",
                f"Approx return: {aud_amount(airline_cache['qantas']['per_direction_aud'])} pp",
                f"Brisbane → Narita anchor: {aud_amount(cost_bounds(airline_cache['qantas']['round_trip_aud'])[0])} return pp",
            ],
            "notes": f"This is the middle direct benchmark between Jetstar and JAL. The Haneda listing pushed closer to {aud_amount(cost_bounds(airline_cache['qantas']['round_trip_aud'])[1])}, which is why the planning band is wider than the Narita-only fare.",
            "source_ids": ["S52", "S53"],
        },
        {
            "category": "Flights",
            "item": "Japan Airlines direct Brisbane ↔ Tokyo",
            "per_person": aud_amount(airline_cache["jal"]["round_trip_aud"]),
            "family": aud_amount(family_cost(airline_cache["jal"]["round_trip_aud"])),
            "details": [
                f"Approx outbound: {aud_amount(airline_cache['jal']['per_direction_aud'])} pp",
                f"Approx return: {aud_amount(airline_cache['jal']['per_direction_aud'])} pp",
                f"Near-season published examples: {aud_amount(airline_cache['jal']['round_trip_aud'])} return pp",
            ],
            "notes": "Still the cleanest premium-style direct reference, but no longer the only reference in the guide.",
            "source_ids": ["S41"],
        },
        {
            "category": "Flights",
            "item": "Philippine Airlines Brisbane ↔ Tokyo",
            "per_person": aud_amount(airline_cache["philippine"]["round_trip_aud"]),
            "family": aud_amount(family_cost(airline_cache["philippine"]["round_trip_aud"])),
            "details": [
                f"Approx outbound: {aud_amount(airline_cache['philippine']['per_direction_aud'])} pp",
                f"Approx return: {aud_amount(airline_cache['philippine']['per_direction_aud'])} pp",
                f"Family of 4: {aud_amount(family_cost(airline_cache['philippine']['round_trip_aud']))}",
            ],
            "notes": "Cheapest full-service one-stop fare I could verify from Brisbane. This is the main reason the guide should not frame JAL as the only serious benchmark.",
            "source_ids": ["S55"],
        },
        {
            "category": "Flights",
            "item": "Cathay Pacific Brisbane ↔ Tokyo",
            "per_person": aud_amount(airline_cache["cathay"]["round_trip_aud"]),
            "family": aud_amount(family_cost(airline_cache["cathay"]["round_trip_aud"])),
            "details": [
                f"Approx outbound: {aud_amount(airline_cache['cathay']['per_direction_aud'])} pp",
                f"Approx return: {aud_amount(airline_cache['cathay']['per_direction_aud'])} pp",
                f"Family of 4: {aud_amount(family_cost(airline_cache['cathay']['round_trip_aud']))}",
            ],
            "notes": "One-stop via Hong Kong. This looks like a better full-service value point than Singapore Airlines if your only goal is lowering the fare bill.",
            "source_ids": ["S54"],
        },
        {
            "category": "Flights",
            "item": "Singapore Airlines Brisbane ↔ Tokyo",
            "per_person": aud_amount(airline_cache["singapore"]["round_trip_aud"]),
            "family": aud_amount(family_cost(airline_cache["singapore"]["round_trip_aud"])),
            "details": [
                f"Approx outbound: {aud_amount(airline_cache['singapore']['per_direction_aud'])} pp",
                f"Approx return: {aud_amount(airline_cache['singapore']['per_direction_aud'])} pp",
                f"Family of 4: {aud_amount(family_cost(airline_cache['singapore']['round_trip_aud']))}",
            ],
            "notes": "A good airline, but not a cheap one in the current Brisbane-origin checks. It is more useful as a stopover choice than as a fare-saving strategy.",
            "source_ids": ["S56"],
        },
        {
            "category": "Flights",
            "item": "Brisbane → Singapore → Tokyo, then Tokyo → Brisbane economy",
            "per_person": aud_amount(singapore_stopover_round_trip_aud),
            "family": aud_amount(family_cost(singapore_stopover_round_trip_aud)),
            "details": [
                f"Brisbane → Singapore: {aud_amount(stopover_cache['brisbane_to_singapore_aud'])} pp",
                f"Singapore → Tokyo: {sgd_to_aud(stopover_cache['singapore_to_tokyo_sgd'])} pp",
                f"Tokyo → Brisbane direct: {aud_amount(stopover_cache['tokyo_to_brisbane_direct_aud'])} pp",
            ],
            "notes": "Flight-only estimate for the stopover version. This still excludes the added Singapore hotel and food spend, which is why I would not present it as the budget option.",
            "source_ids": ["S30", "S43", "S44", "S45", "S46", "S47", "S56"],
        },
        {
            "category": "Flight leg",
            "item": "Brisbane → Tokyo direct",
            "per_person": aud_amount(direct_per_direction_aud),
            "family": aud_amount(family_cost(direct_per_direction_aud)),
            "details": [
                f"Jetstar planning anchor: {aud_amount(airline_cache['jetstar']['per_direction_aud'])} pp",
                f"Qantas planning anchor: {aud_amount(airline_cache['qantas']['per_direction_aud'])} pp",
                f"JAL planning anchor: {aud_amount(airline_cache['jal']['per_direction_aud'])} pp",
            ],
            "notes": "Per-direction planning band across the direct airlines now covered in the guide.",
            "source_ids": ["S41", "S50", "S52", "S53"],
        },
        {
            "category": "Flight leg",
            "item": "Tokyo → Brisbane direct",
            "per_person": aud_amount(direct_per_direction_aud),
            "family": aud_amount(family_cost(direct_per_direction_aud)),
            "details": [
                f"Jetstar planning anchor: {aud_amount(airline_cache['jetstar']['per_direction_aud'])} pp",
                f"Qantas planning anchor: {aud_amount(airline_cache['qantas']['per_direction_aud'])} pp",
                f"JAL planning anchor: {aud_amount(airline_cache['jal']['per_direction_aud'])} pp",
            ],
            "notes": "Using symmetric half-fare planning math here is an inference, because several airline pages publish cleaner round-trip examples than true one-way Tokyo-origin fares.",
            "source_ids": ["S41", "S51", "S52", "S53"],
        },
        {
            "category": "Flight leg",
            "item": "Brisbane → Singapore",
            "per_person": aud_amount(stopover_cache["brisbane_to_singapore_aud"]),
            "family": aud_amount(family_cost(stopover_cache["brisbane_to_singapore_aud"])),
            "notes": "One-way stopover-leg estimate.",
            "source_ids": ["S43", "S46"],
        },
        {
            "category": "Flight leg",
            "item": "Singapore → Tokyo",
            "per_person": sgd_to_aud(stopover_cache["singapore_to_tokyo_sgd"]),
            "family": aud_amount(family_cost(sgd_to_aud_value(stopover_cache["singapore_to_tokyo_sgd"]))),
            "notes": f"Converted from Singapore-dollar pricing using S$1 = AUD {SGD_TO_AUD:.2f}.",
            "source_ids": ["S44", "S45", "S47"],
        },
    ]

    for segment in intercity_segments:
        finance_rows.append(
            {
                "category": "Intercity transport",
                "item": f"{segment['from']} → {segment['to']}",
                "per_person": segment["adult_cost_label"],
                "family": segment["family_cost_label"],
                "notes": f"{segment['mode']}; {segment['duration']}.",
                "source_ids": segment["source_ids"],
            }
        )

    for row in day_trip_rows:
        finance_rows.append(
            {
                "category": "Day-trip transport",
                "item": f"{row['base']} → {row['trip']}",
                "per_person": row["adult_cost_label"],
                "family": row["family_cost_label"],
                "notes": row["notes"],
                "source_ids": row["source_ids"],
            }
        )

    for food in food_budgets:
        finance_rows.append(
            {
                "category": "Daily food",
                "item": f"{food['location']} per day",
                "per_person": food["per_person_label"],
                "family": food["family_of_four_label"],
                "notes": food["day_trip_add_on"],
                "source_ids": food["source_ids"],
            }
        )

    finance_rows.extend(
        [
            {
                "category": "Activity",
                "item": "Yayoi Kusama Museum",
                "per_person": money(activity_cache["yayoi_kusama_adult_jpy"]),
                "family": money(family_cost(activity_cache["yayoi_kusama_adult_jpy"])),
                "notes": "Adult price. Children 6-18 are cheaper; under 6 free.",
                "source_ids": ["S32"],
            },
            {
                "category": "Activity",
                "item": "Cup Noodles Museum Osaka Ikeda",
                "per_person": f"Entry free; My CUPNOODLES Factory {money(activity_cache['cupnoodles_factory_jpy'])}",
                "family": f"Entry free; My CUPNOODLES Factory {money(family_cost(activity_cache['cupnoodles_factory_jpy']))}",
                "notes": "Museum entry is free; attraction cost is for the custom cup activity.",
                "source_ids": ["S37"],
            },
            {
                "category": "Activity",
                "item": "Hungry Osaka food tour",
                "per_person": money(activity_cache["hungry_osaka_food_tour_jpy"]),
                "family": money(family_cost(activity_cache["hungry_osaka_food_tour_jpy"])),
                "notes": "Small-group Shinsekai food tour.",
                "source_ids": ["S36"],
            },
            {
                "category": "Activity",
                "item": "Oedo Antique Market",
                "per_person": "Free",
                "family": "Free",
                "notes": "No ticket cost, but shopping spend varies.",
                "source_ids": ["S34", "S40"],
            },
        ]
    )

    return {
        "meta": {
            "title": "Japan Family Trip Guide",
            "subtitle": "Tokyo, Osaka, Hiroshima, Kanazawa, Takayama, Nagano, then Tokyo again",
            "travel_window": "October 28, 2026 to November 17, 2026",
            "family_size": 4,
            "family_assumption": "All transport family totals assume four adult-equivalent fares. Real family cost can be lower if some travelers qualify for child pricing.",
            "high_level_summary": "This version assumes 20 nights total: 4 Tokyo, 4 Osaka, 3 Hiroshima, 2 Kanazawa, 2 Takayama, 2 Nagano, and 3 final nights in Tokyo.",
            "city_focus_days": city_focus_days,
            "excursion_days": excursion_days,
            "source_checked_date": financial_cache["source_checked_date"],
            "fx": {
                "date": FX_DATE,
                "aud_jpy_close": f"{AUD_JPY_CLOSE:.2f}",
                "source_id": "S23",
            },
        },
        "overview_cards": [
            {
                "label": "Intercity transport",
                "value": money(family_cost(mid_intercity_total)),
                "detail": f"About {money(mid_intercity_total)} per adult across the full route",
            },
            {
                "label": "Food per day",
                "value": money(
                    (
                        min(cost_bounds(food["family_of_four"])[0] for food in food_budgets),
                        max(cost_bounds(food["family_of_four"])[1] for food in food_budgets),
                    )
                ),
                "detail": "Typical family-of-four daily band across these stops",
            },
            {
                "label": "Time in Japan",
                "value": "20 nights / 19 full days",
                "detail": "21 calendar dates touched in Japan if you land Oct 28 and fly out Nov 17",
            },
            {
                "label": "Split",
                "value": f"{city_focus_days} city / {excursion_days} out-of-city",
                "detail": "Close to a 50/50 sightseeing mix without making the route feel frantic",
            },
        ],
        "japan_time_math": japan_time_math,
        "flight_options": flight_options,
        "flight_market_rows": flight_market_rows,
        "dates_and_times_rows": dates_and_times_rows,
        "finance_rows": finance_rows,
        "language_core_rows": language_core_rows,
        "language_ideas_rows": language_ideas_rows,
        "requested_highlights": requested_highlights,
        "itinerary_rows": [
            {"dates": "Oct 28-Nov 1", "base": "Tokyo", "nights": 4, "rhythm": "Big-city landing, keep this block light, save Kusama/Oedo/Koedo for final Tokyo"},
            {"dates": "Nov 1-Nov 5", "base": "Osaka", "nights": 4, "rhythm": "2 city days, Kyoto or Nara, Hungry Osaka evening, Cup Noodles Ikeda half-day"},
            {"dates": "Nov 5-Nov 8", "base": "Hiroshima", "nights": 3, "rhythm": "1 core city day, 1 Miyajima day, 1 flex day"},
            {"dates": "Nov 8-Nov 10", "base": "Kanazawa", "nights": 2, "rhythm": "1 compact city day, 1 Shirakawa-go day or transfer stop"},
            {"dates": "Nov 10-Nov 12", "base": "Takayama", "nights": 2, "rhythm": "1 old-town day, 1 Hida side trip"},
            {"dates": "Nov 12-Nov 14", "base": "Nagano", "nights": 2, "rhythm": "1 Zenkoji day, 1 Snow Monkey day"},
            {"dates": "Nov 14-Nov 17", "base": "Tokyo", "nights": 3, "rhythm": "Yoyogi/Tomigaya stay, Kusama, Oedo on Nov 15, Nippori, Koedo on Nov 16"},
        ],
        "intercity_segments": intercity_segments,
        "day_trip_rows": day_trip_rows,
        "food_budgets": food_budgets,
        "stays": stays,
        "citations": citations,
        "citations_by_id": citation_index(citations),
        "maps": day_trip_maps,
    }


def render_site(data: dict) -> str:
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template("site.html.j2")
    return template.render(data=data, maps_json=json.dumps(data["maps"]))


def write_site(html: str) -> None:
    OUT_DIR.mkdir(exist_ok=True)
    DOCS_DIR.mkdir(exist_ok=True)
    (DOCS_DIR / "assets").mkdir(exist_ok=True)

    out_file = OUT_DIR / "japan-family-trip-guide.html"
    docs_file = DOCS_DIR / "index.html"
    css_src = ASSETS_DIR / "site.css"
    css_dest = DOCS_DIR / "assets" / "site.css"

    out_file.write_text(html, encoding="utf-8")
    docs_file.write_text(html, encoding="utf-8")
    shutil.copyfile(css_src, css_dest)
    (DOCS_DIR / ".nojekyll").write_text("", encoding="utf-8")


def main() -> None:
    data = build_data()
    html = render_site(data)
    write_site(html)
    print(f"Wrote {OUT_DIR / 'japan-family-trip-guide.html'}")
    print(f"Wrote {DOCS_DIR / 'index.html'}")


if __name__ == "__main__":
    main()
