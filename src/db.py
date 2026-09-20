"""MongoDB-yhteys ja kävijähavaintojen tallennus."""

import os
from datetime import datetime

from dotenv import load_dotenv
from dateutil import parser as date_parser
from pymongo import ASCENDING, DESCENDING, MongoClient
from pymongo.collection import Collection
from pymongo.errors import PyMongoError

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "aiot_occupancy")
MONGODB_COLLECTION = os.getenv("MONGODB_COLLECTION", "occupancy")

_client: MongoClient | None = None


def normalize_timestamp(timestamp: str | datetime) -> datetime:
    """Muuntaa MQTT:n aikaleiman MongoDB:n natiiviksi päivämääräarvoksi."""
    parsed = timestamp if isinstance(timestamp, datetime) else date_parser.parse(timestamp)
    return parsed.astimezone() if parsed.tzinfo is None else parsed


def get_collection() -> Collection:
    """Palauttaa MongoDB-kokoelman tai kertoo selkeästi puuttuvista asetuksista."""
    global _client

    if not MONGODB_URI:
        raise RuntimeError(
            "MONGODB_URI puuttuu. Lisää MongoDB-yhteysosoite projektin .env-tiedostoon."
        )

    if _client is None:
        _client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)

    return _client[MONGODB_DATABASE][MONGODB_COLLECTION]


def init_db() -> None:
    """Tarkistaa MongoDB-yhteyden ja luo kyselyjä nopeuttavat indeksit."""
    try:
        collection = get_collection()
        collection.database.client.admin.command("ping")
        collection.create_index([("timestamp", DESCENDING)])
        collection.create_index([("device_id", ASCENDING), ("timestamp", DESCENDING)])
    except PyMongoError as error:
        raise RuntimeError(f"MongoDB-yhteyden alustus epäonnistui: {error}") from error


def insert_record(timestamp: str, device_id: str | None, topic: str, occupancy: int) -> None:
    """Tallentaa yhden MQTT-havainnon MongoDB:n occupancy-kokoelmaan."""
    try:
        get_collection().insert_one(
            {
                "timestamp": normalize_timestamp(timestamp),
                "device_id": device_id,
                "topic": topic,
                "occupancy": int(occupancy),
                "received_at": datetime.now().astimezone(),
            }
        )
    except PyMongoError as error:
        raise RuntimeError(f"Havainnon tallennus MongoDB:hen epäonnistui: {error}") from error
