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
OUT_DIR = ROOT / "out"
DOCS_DIR = ROOT / "docs"
FX_DATE = "2026-03-12"
AUD_JPY_CLOSE = 113.46
JPY_TO_AUD = 1 / AUD_JPY_CLOSE
SGD_AUD_FX_DATE = "2026-03-12"
SGD_TO_AUD = 1.10


def yen(value: int | tuple[int, int]) -> str:
    if isinstance(value, tuple):
        return f"JPY {value[0]:,}-{value[1]:,}"
    return f"JPY {value:,}"


def aud(value: int | tuple[int, int]) -> str:
    if isinstance(value, tuple):
        return f"AUD {value[0] * JPY_TO_AUD:,.2f}-{value[1] * JPY_TO_AUD:,.2f}"
    return f"AUD {value * JPY_TO_AUD:,.2f}"


def money(value: int | tuple[int, int]) -> str:
    return f"{yen(value)} / {aud(value)}"


def aud_amount(value: int | float | tuple[int | float, int | float]) -> str:
    if isinstance(value, tuple):
        return f"AUD {value[0]:,.0f}-{value[1]:,.0f}"
    return f"AUD {value:,.0f}"


def sgd_to_aud(value: int | float | tuple[int | float, int | float]) -> str:
    if isinstance(value, tuple):
        return aud_amount((value[0] * SGD_TO_AUD, value[1] * SGD_TO_AUD))
    return aud_amount(value * SGD_TO_AUD)


def family_cost(value: int | tuple[int, int], family_size: int = 4) -> int | tuple[int, int]:
    if isinstance(value, tuple):
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
            "note": "FX basis for AUD conversion. This guide uses the latest verified market close I could confirm in-session: AUD/JPY 113.46 on March 12, 2026.",
        },
        {
            "id": "S24",
            "title": "Woolloongabba to Brisbane Airport (BNE)",
            "publisher": "Rome2Rio",
            "url": "https://www.rome2rio.com/s/Woolloongabba/Brisbane-Airport-BNE",
            "accessed": "2026-03-18",
            "note": "Used for Woolloongabba to Brisbane Airport public-transport timing.",
        },
        {
            "id": "S25",
            "title": "Driving time from Woolloongabba to BNE",
            "publisher": "Travelmath",
            "url": "https://www.travelmath.com/driving-time/from/Woolloongabba%2C%2BAustralia/to/BNE",
            "accessed": "2026-03-18",
            "note": "Used for a typical driving-time estimate from Woolloongabba to Brisbane Airport.",
        },
        {
            "id": "S26",
            "title": "Sumner to Brisbane Airport (BNE)",
            "publisher": "Rome2Rio",
            "url": "https://www.rome2rio.com/s/Sumner-QLD-Australia/Brisbane-Airport-BNE",
            "accessed": "2026-03-18",
            "note": "Used for Sumner to Brisbane Airport drive and public-transport timing.",
        },
        {
            "id": "S27",
            "title": "Haneda Airport - getting there, terminal info, and more",
            "publisher": "GO TOKYO",
            "url": "https://www.gotokyo.org/en/plan/airport-access/haneda-airport/",
            "accessed": "2026-03-18",
            "note": "Official Tokyo tourism guidance for Haneda to central Tokyo access times.",
        },
        {
            "id": "S28",
            "title": "Narita International Airport - getting there, terminal info, and more",
            "publisher": "GO TOKYO",
            "url": "https://www.gotokyo.org/en/plan/airport-access/narita-airport/index.html",
            "accessed": "2026-03-18",
            "note": "Official Tokyo tourism guidance for Narita to central Tokyo access times.",
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
    ]

    intercity_segments = [
        {
            "from": "Tokyo",
            "to": "Osaka",
            "mode": "Nozomi Shinkansen",
            "duration": "about 2h 30m",
            "adult_cost": 14520,
            "family_cost": family_cost(14520),
            "notes": "Reserved-seat planning fare using smartEX. This is the cleanest, fastest long jump in the trip.",
            "source_ids": ["S01", "S22"],
            "map_points": ["Tokyo Station", "Shin-Osaka Station"],
        },
        {
            "from": "Osaka",
            "to": "Hiroshima",
            "mode": "Nozomi Shinkansen",
            "duration": "about 1h 25m",
            "adult_cost": 10750,
            "family_cost": family_cost(10750),
            "notes": "Reserved-seat planning fare using smartEX from Shin-Osaka to Hiroshima.",
            "source_ids": ["S01"],
            "map_points": ["Shin-Osaka Station", "Hiroshima Station"],
        },
        {
            "from": "Hiroshima",
            "to": "Kanazawa",
            "mode": "Rail via Osaka/Tsuruga",
            "duration": "about 5h",
            "adult_cost": (16190, 23470),
            "family_cost": family_cost((16190, 23470)),
            "notes": "Estimate range from online route planners because this trip spans multiple operators and seat choices. Use a mid-range budget if you want reserved seats without over-optimizing.",
            "source_ids": ["S21"],
            "map_points": ["Hiroshima Station", "Kanazawa Station"],
        },
        {
            "from": "Kanazawa",
            "to": "Takayama",
            "mode": "Direct highway bus",
            "duration": "about 3h 30m",
            "adult_cost": 4200,
            "family_cost": family_cost(4200),
            "notes": "Bus is usually the best fit here. It is also the cleanest way to fold Shirakawa-go into the route if you prefer a stopover instead of a separate day trip.",
            "source_ids": ["S12"],
            "map_points": ["Kanazawa Station", "Takayama Station"],
        },
        {
            "from": "Takayama",
            "to": "Nagano",
            "mode": "Bus to Matsumoto + train to Nagano",
            "duration": "about 4h 15m",
            "adult_cost": 6720,
            "family_cost": family_cost(6720),
            "notes": "Planning number combines Takayama to Matsumoto and Matsumoto to Nagano. This is a practical regional connection, not a single through fare.",
            "source_ids": ["S19"],
            "map_points": ["Takayama Station", "Matsumoto Station", "Nagano Station"],
        },
        {
            "from": "Nagano",
            "to": "Tokyo",
            "mode": "Hokuriku Shinkansen",
            "duration": "about 1h 30m",
            "adult_cost": 7680,
            "family_cost": family_cost(7680),
            "notes": "Planning fare based on the standard Tokyo-Nagano bullet train fare published in Matsumoto access guidance.",
            "source_ids": ["S19"],
            "map_points": ["Nagano Station", "Tokyo Station"],
        },
    ]

    day_trip_rows = [
        {
            "base": "Tokyo",
            "trip": "Nikko",
            "adult_cost": 8000,
            "family_cost": family_cost(8000),
            "notes": "NIKKO PASS All Area; limited express surcharge extra if you want a faster train.",
            "source_ids": ["S03"],
        },
        {
            "base": "Tokyo",
            "trip": "Hakone",
            "adult_cost": 7100,
            "family_cost": family_cost(7100),
            "notes": "Hakone Freepass sample price from Shinjuku. It is a 2-day pass, so treat this as a convenience ceiling rather than the cheapest possible 1-day outing.",
            "source_ids": ["S04"],
        },
        {
            "base": "Osaka",
            "trip": "Kyoto",
            "adult_cost": 1900,
            "family_cost": family_cost(1900),
            "notes": "KINTETSU RAIL PASS 1-day price. Good planning number if you want a simple rail-only sightseeing day.",
            "source_ids": ["S06", "S07"],
        },
        {
            "base": "Osaka",
            "trip": "Nara",
            "adult_cost": 1900,
            "family_cost": family_cost(1900),
            "notes": "Same KINTETSU RAIL PASS 1-day planning number; useful if you want Nara without fiddling with separate tickets.",
            "source_ids": ["S06", "S08"],
        },
        {
            "base": "Hiroshima",
            "trip": "Miyajima",
            "adult_cost": 1300,
            "family_cost": family_cost(1300),
            "notes": "Estimate for Hiroshima city to Miyajima by local rail/tram plus ferry and island visitor tax. Ferry fare itself is official.",
            "source_ids": ["S09", "S10"],
        },
        {
            "base": "Kanazawa",
            "trip": "Shirakawa-go",
            "adult_cost": 5600,
            "family_cost": family_cost(5600),
            "notes": "Round-trip direct bus using the official Kanazawa/Shirakawa-go fare table.",
            "source_ids": ["S12"],
        },
        {
            "base": "Takayama",
            "trip": "Hida Furukawa",
            "adult_cost": (540, 720),
            "family_cost": family_cost((540, 720)),
            "notes": "Low-friction rail estimate for the 15-minute hop each way. If you want a bundled food-and-sake outing, local tourism packages run higher.",
            "source_ids": ["S14", "S15"],
        },
        {
            "base": "Nagano",
            "trip": "Snow Monkey Park",
            "adult_cost": (3960, 4000),
            "family_cost": family_cost((3960, 4000)),
            "notes": "Late-October and November travelers should assume separate transport because current 2026 guidance says the pass is not sold in October or November.",
            "source_ids": ["S16", "S17", "S18"],
        },
    ]

    airport_access = [
        {
            "phase": "Departure day",
            "route": "Woolloongabba → Brisbane International Airport",
            "best_for": "fastest road option",
            "timing": "about 17 min by car",
            "notes": "Fast if you have a family drop-off or taxi. Traffic can obviously move this around, especially in the morning peak.",
            "source_ids": ["S25"],
            "map_points": ["Woolloongabba QLD", "Brisbane International Airport"],
        },
        {
            "phase": "Departure day",
            "route": "Woolloongabba → Brisbane International Airport",
            "best_for": "public transport",
            "timing": "about 34 min by train",
            "notes": "Rome2Rio shows a direct rail option from Boggo Road to the International Airport station, which is the cleanest non-car choice.",
            "source_ids": ["S24"],
            "map_points": ["Boggo Road Station", "Brisbane International Airport"],
        },
        {
            "phase": "Departure day",
            "route": "Sumner → Brisbane International Airport",
            "best_for": "fastest road option",
            "timing": "about 26 min by car",
            "notes": "This is the practical family option from Sumner if you are trying to keep the airport leg simple.",
            "source_ids": ["S26"],
            "map_points": ["Sumner QLD", "Brisbane International Airport"],
        },
        {
            "phase": "Departure day",
            "route": "Sumner → Brisbane International Airport",
            "best_for": "public transport",
            "timing": "about 1h 3m by train",
            "notes": "Rome2Rio shows the train as the best public-transport option, typically via Darra and Eagle Junction.",
            "source_ids": ["S26"],
            "map_points": ["Sumner Station", "Brisbane International Airport"],
        },
        {
            "phase": "Arrival day in Japan",
            "route": "Haneda Airport → Tokyo Station / central Tokyo",
            "best_for": "fastest rail arrival",
            "timing": "about 20-24 min by train",
            "notes": "Official GO TOKYO guidance puts Haneda Terminal 3 at 13 minutes to Hamamatsucho plus 7 minutes to Tokyo Station, or roughly 24 minutes via Shinagawa. If you can choose airports, Haneda is materially easier for a family arrival day.",
            "source_ids": ["S27"],
            "map_points": ["Haneda Airport Terminal 3", "Tokyo Station"],
        },
        {
            "phase": "Arrival day in Japan",
            "route": "Narita Airport → Tokyo Station / central Tokyo",
            "best_for": "most predictable rail arrival",
            "timing": "about 60 min by Narita Express",
            "notes": "Official GO TOKYO guidance puts Narita Express at about 60 minutes to Tokyo Station. The airport bus can be as fast as 68 minutes but is more traffic-sensitive.",
            "source_ids": ["S28"],
            "map_points": ["Narita International Airport", "Tokyo Station"],
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
            "flight_cost": aud_amount((1700, 1850)),
            "family_cost": aud_amount((6800, 7400)),
            "price_breakdown": [
                "Brisbane → Tokyo direct: AUD 850-925 pp",
                "Tokyo → Brisbane direct: AUD 850-925 pp",
            ],
            "japan_time": "20 nights / 19 full days in Japan",
            "notes": "Use this if Japan is the priority. Current JAL pricing suggests direct economy is roughly in this band round-trip per person for planning purposes.",
            "source_ids": ["S29", "S30", "S41", "S42"],
        },
        {
            "name": "Singapore stopover outbound",
            "pattern": "Brisbane → Singapore, 2 nights in Singapore, then Singapore → Tokyo; return Tokyo → Brisbane direct",
            "air_time": "about 7h 40m-8h 00m to Singapore, 6h 30m-6h 35m to Tokyo, then 8h 50m-9h 05m home",
            "flight_cost": aud_amount((1650, 1850)),
            "family_cost": aud_amount((6600, 7400)),
            "price_breakdown": [
                "Brisbane → Singapore: AUD 400-450 pp",
                f"Singapore → Tokyo: {sgd_to_aud((352, 450))} pp",
                "Tokyo → Brisbane direct: AUD 850-950 pp",
            ],
            "japan_time": "18 nights / 17 full days in Japan",
            "notes": f"Flight-only cost is broadly similar to the direct option once you estimate one-way pricing from current round-trip fares. Brisbane-Singapore is around {aud_amount((400, 450))} pp one-way; Singapore-Tokyo works out to about {sgd_to_aud((352, 450))} pp one-way using S$1 = AUD {SGD_TO_AUD:.2f}; Tokyo-Brisbane direct is roughly {aud_amount((850, 950))} pp one-way. The tradeoff is that you lose 2 Japan nights and still need to pay for 2 Singapore hotel nights plus food.",
            "source_ids": ["S30", "S43", "S44", "S45", "S46", "S47"],
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
            "cost": f"{money(1100)} adult",
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
            "cost": f"Osaka Ikeda entry free; My CUPNOODLES Factory {money(500)} each",
            "notes": "Osaka Ikeda is the cleaner fit than Yokohama for this route. The official site says it is about 20 minutes from Hankyu Osaka-Umeda to Ikeda Station, then about a 5-minute walk. Keep Yokohama as a backup only if you later rebalance Tokyo.",
            "source_ids": ["S37", "S38"],
        },
        {
            "title": "Hungry Osaka food walking tour",
            "base": "Osaka",
            "best_slot": "Evening on Nov 2 or Nov 3, 2026",
            "cost": f"{money(13000)} pp",
            "notes": "This is a direct match for your food-first Osaka stop. Official tour details: 3 to 3.5 hours, 15 dishes, 3 drinks, Shinsekai focus, and meeting outside Ebisucho Station Exit 3.",
            "source_ids": ["S36"],
        },
    ]

    food_budgets = [
        {
            "location": "Tokyo",
            "per_person": (3500, 6000),
            "family_of_four": family_cost((3500, 6000)),
            "day_trip_add_on": f"+{money((500, 1000))} pp on Nikko/Hakone days",
            "notes": "Tokyo is the priciest base in this route, but casual food is still good value if you mix konbini breakfasts, lunch sets, and one proper dinner.",
            "source_ids": ["S20"],
        },
        {
            "location": "Osaka",
            "per_person": (3200, 5500),
            "family_of_four": family_cost((3200, 5500)),
            "day_trip_add_on": f"+{money(500)} pp on Kyoto/Nara days",
            "notes": "Osaka is a strong food city with many affordable casual meals, so this is a little softer than Tokyo.",
            "source_ids": ["S20", "S05"],
        },
        {
            "location": "Hiroshima",
            "per_person": (3200, 5200),
            "family_of_four": family_cost((3200, 5200)),
            "day_trip_add_on": f"+{money(500)} pp on Miyajima day",
            "notes": "City meals are moderate; seafood-heavy or shrine-area lunches on Miyajima push the upper end.",
            "source_ids": ["S20", "S09"],
        },
        {
            "location": "Kanazawa",
            "per_person": (3500, 6000),
            "family_of_four": family_cost((3500, 6000)),
            "day_trip_add_on": f"+{money(500)} pp on Shirakawa-go day",
            "notes": "Seafood and market lunches can easily nudge this upward, but standard family dining still fits this band.",
            "source_ids": ["S20", "S11"],
        },
        {
            "location": "Takayama",
            "per_person": (3500, 6500),
            "family_of_four": family_cost((3500, 6500)),
            "day_trip_add_on": f"+{money((300, 700))} pp if you add sake or Hida beef tastings",
            "notes": "Takayama is compact but tourist-oriented. Hida beef snacks, sake tastings, and ryokan upgrades move this quickly.",
            "source_ids": ["S20", "S13"],
        },
        {
            "location": "Nagano",
            "per_person": (3000, 5200),
            "family_of_four": family_cost((3000, 5200)),
            "day_trip_add_on": f"+{money(500)} pp on Snow Monkey day",
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
                    "adult_cost": 8000,
                    "family_cost": family_cost(8000),
                    "duration": "full day",
                    "notes": "Best if you want shrines, mountain scenery, and a completely different rhythm from Tokyo.",
                    "source_ids": ["S03"],
                    "map_points": ["Asakusa Station", "Tobu Nikko Station"],
                },
                {
                    "name": "Hakone",
                    "coord": [35.2323, 139.1069],
                    "transport": "Odakyu from Shinjuku",
                    "adult_cost": 7100,
                    "family_cost": family_cost(7100),
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
                    "adult_cost": 1900,
                    "family_cost": family_cost(1900),
                    "duration": "full day",
                    "notes": "Use Kyoto for temples, old lanes, and a different cultural tone. Pick one Kyoto zone rather than trying to conquer the whole city in a day.",
                    "source_ids": ["S06", "S07"],
                    "map_points": ["Osaka-Namba Station", "Kyoto Station"],
                },
                {
                    "name": "Nara",
                    "coord": [34.6851, 135.8048],
                    "transport": "Rail from Osaka",
                    "adult_cost": 1900,
                    "family_cost": family_cost(1900),
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
                    "adult_cost": 1300,
                    "family_cost": family_cost(1300),
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
                    "adult_cost": 5600,
                    "family_cost": family_cost(5600),
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
                    "adult_cost": (540, 720),
                    "family_cost": family_cost((540, 720)),
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
                    "adult_cost": (3960, 4000),
                    "family_cost": family_cost((3960, 4000)),
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

    for row in airport_access:
        row["maps_url"] = build_google_maps_direction(row["map_points"])

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
        if isinstance(segment["adult_cost"], tuple):
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
            "source_checked_date": "March 18, 2026",
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
                "value": money((12000, 26000)),
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
        "airport_access": airport_access,
        "japan_time_math": japan_time_math,
        "flight_options": flight_options,
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
