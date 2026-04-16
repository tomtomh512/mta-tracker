from google.transit import gtfs_realtime_pb2
import requests

def fetch_feed(url: str) -> gtfs_realtime_pb2.FeedMessage | None:
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        feed = gtfs_realtime_pb2.FeedMessage()
        feed.ParseFromString(response.content)
        return feed

    except Exception as e:
        print(f"Failed to fetch feed {url}: {e}")
        return None

# for some reason trip id from url doesnt match static trip ids
# must check if trip id from url is contained in static trip id
def match_static_trip(trip_id_from_url: str, valid_trip_ids: set[str]):
    for valid_id in valid_trip_ids:
        if trip_id_from_url in valid_id:
            return valid_id

    return None