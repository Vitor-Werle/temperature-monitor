from datetime import datetime
from pymongo import MongoClient

MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "temperature-monitor"
SOURCE_COLLECTION = "sensor_data"
TARGET_COLLECTION = "daily_summary"

mongo_client = MongoClient(MONGO_URI)
db = mongo_client[DB_NAME]
source_collection = db[SOURCE_COLLECTION]
target_collection = db[TARGET_COLLECTION]


def parse_timestamp(value):
    """Converte o campo timestamp em objeto datetime."""
    if value is None:
        return None

    if isinstance(value, datetime):
        return value

    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None

    return None


def build_daily_summary():
    """Agrupa os dados por dia e salva o resumo diário em outra collection."""
    daily_data = {}

    for doc in source_collection.find({
        "temperature": {"$exists": True},
        "timestamp": {"$exists": True}
    }):
        temperature = doc.get("temperature")
        if temperature is None:
            continue

        timestamp = parse_timestamp(doc.get("timestamp"))
        if timestamp is None:
            continue

        day = timestamp.date().isoformat()

        if day not in daily_data:
            daily_data[day] = {
                "sum": 0.0,
                "count": 0,
                "min": float("inf"),
                "max": float("-inf")
            }

        temp_value = float(temperature)
        daily_data[day]["sum"] += temp_value
        daily_data[day]["count"] += 1
        daily_data[day]["min"] = min(daily_data[day]["min"], temp_value)
        daily_data[day]["max"] = max(daily_data[day]["max"], temp_value)

    if not daily_data:
        print("Nenhum dado encontrado para gerar o resumo diário.")
        return []

    summaries = []
    for day, values in sorted(daily_data.items()):
        avg_temperature = values["sum"] / values["count"]
        summary = {
            "day": day,
            "max_temperature": round(values["max"], 2),
            "min_temperature": round(values["min"], 2),
            "avg_temperature": round(avg_temperature, 2),
            "readings_count": values["count"],
            "updated_at": datetime.utcnow()
        }

        target_collection.update_one(
            {"day": day},
            {"$set": summary},
            upsert=True
        )
        summaries.append(summary)
        print(f"Resumo do dia {day}: min={summary['min_temperature']} | max={summary['max_temperature']} | avg={summary['avg_temperature']}")

    print(f"Resumo diário salvo na collection '{TARGET_COLLECTION}'.")
    return summaries


if __name__ == "__main__":
    build_daily_summary()
