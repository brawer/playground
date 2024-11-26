# Draft for a script ("spider") to import Swiss public transit stations
# from OpenTransportData.swiss to AllThePlaces.xyz for eventual matching
# with OpenStreetMap.
#
# Other than the real spider, this script does not depend on the
# (pretty large) framework used by AllThePlaces. Therefore, this
# script cannot run as-is inside AllThePlaces. But it's very close to
# the real code, and the needed changes for integration will be
# trivial.  Development is easier without having to start up the big
# framework, hence this draft script.
#
# Description of the upstream data model:
# https://opentransportdata.swiss/en/cookbook/service-points/
#
# Usage: Run this script without any argouments.
# Output: A file called "out.geojson".

import collections
import csv
import datetime
import io
import json
import os
import urllib.request
import zipfile


def _prepare_tags_table(t):
    return {
        key: tuple(tuple(tag.split("=", 1)) for tag in value.split())
        for key, value in t.items()
    }


# Tags we emit for transit stations based on the primary mode of transport.
# For planned or disused stations, the spider will prepend a lifecycle
# tag to the first key, resulting in tags like "planned:highway=elevator".
PRIMARY_STATION_TAGS = _prepare_tags_table(
    {
        "BOAT": "amenity=ferry_terminal",
        "BUS": "highway=bus_stop",
        "CABLE_CAR": "railway=station funicular=yes",
        "CABLE_RAILWAY": "railway=station funicular=yes",
        "CHAIRLIFT": "aerialway=station",
        "ELEVATOR": "highway=elevator",
        "METRO": "railway=station subway=yes",
        "RACK_RAILWAY": "railway=station rack=yes",
        "TRAIN": "railway=station",
    }
)


# Tags we emit for transit stations for non-primary modes of transport.
SECONDARY_STATION_TAGS = _prepare_tags_table(
    {
        "BOAT": "ferry=yes",
        "BUS": "bus=yes",
        "CABLE_CAR": "funicular=yes",
        "CABLE_RAILWAY": "funicular=yes",
        "CHAIRLIFT": "aerialway=yes",
        "ELEVATOR": "elevator=yes",
        "METRO": "subway=yes",
        "RACK_RAILWAY": "railway=yes rack=yes",
        "TRAIN": "railway=yes",
    }
)


FakeScrapyResponse = collections.namedtuple("FakeScrapyResponse", "body")


class OpenTransportDataCHSpider(object):
    name = "opentransportdata_ch"
    allowed_domains = ["opentransportdata.swiss"]
    url_pattern = "https://opentransportdata.swiss/en/dataset/%s/permalink"

    # TODO: Change attribution to "optional" once All The Places appears
    # on this list: https://opentransportdata.swiss/en/authorised-databases/
    # Attribution exemption requested on 2024-11-21 by Sascha Brawer.
    dataset_attributes = {
        "attribution": "required",
        "attribution:name:en": "Open Data Platform Mobility Switzerland",
        "attribution:name:de": "Open-Data-Plattform Mobilität Schweiz",
        "attribution:name:fr": "Plateforme open data pour la mobilité en Suisse",
        "attribution:name:it": "Piattaforma open data sulla mobilità in Svizzeraa",
        "attribution:wikidata": "Q97319754",
        "license:website": "https://opentransportdata.swiss/en/terms-of-use/",
        "use:commercial": "yes",
        "use:openstreetmap": "yes",
        "website": "https://opentransportdata.swiss/",
    }

    def __init__(self, exporter):
        self.exporter = exporter

    def start_requests(self):
        self.today = datetime.date.today().isoformat()
        self.stations = {}
        self.station_type_tags = {}
        url = self.url_pattern % "service-points-full"
        # yield scrapy.Request(url, callback=self.extract_stations)
        self.download(url, callback=self.extract_stations)

    # TODO: Remove this method before including in All The Places.
    # In the real setup, fetches are handled by the Scrapy framework.
    def download(self, url, callback):
        zip_path = url.split("/")[-2] + ".zip"
        if not os.path.exists(zip_path):
            print(f"fetching {url}")
            with open(zip_path + ".tmp", "wb") as fp:
                with urllib.request.urlopen(url) as req:
                    fp.write(req.read())  # not atomic
            os.rename(zip_path + ".tmp", zip_path)  # atomic
        features = []
        with open(zip_path, "rb") as fp:
            response = FakeScrapyResponse(fp.read())
            for item in callback(response):
                self.exporter.write(item)

    def extract_stations(self, response):
        for item in self.process_zip(response, self.process_station):
            yield item

        # Since we need some station sttributes to emit platforms
        # with the correct OSM tags, we need to process the stations
        # ("service points") before the platforms ("traffic points").
        # However, Scrapy does not support serializing requests,
        # and the order of handling responses is non-deterministic.
        # So we need to shoeshorn serialization by issuing the
        # follow-up request for the platform file from here.
        url = self.url_pattern % "traffic-points-full"
        # yield scrapy.Request(url, callback=self.extract_traffic_points)
        self.download(url, callback=self.extract_traffic_points)

    def extract_traffic_points(self, response):
        return self.process_zip(response, self.process_platform)

    def process_station(self, r):
        if r.get("status") != "VALIDATED":
            return

        ifopt_id = r["sloid"]
        item = {
            "lat": round(float(r["wgs84North"] or "0"), 8),
            "lon": round(float(r["wgs84East"] or "0"), 8),
            "country": r["isoCountryCode"].upper(),
            "ref": r["sloid"],
            "extras": {
                "ele:regional": round(float(r["height"] or "0"), 2),
                "official_name": self.cleanup_name(r["designationOfficial"]),
                "operator": self.parse_operator(r),
                "ref:IFOPT": ifopt_id,
            },
        }
        item["extras"].update(self.parse_lifecycle(r))
        type_tags = self.parse_station_type(r, item)
        if len(type_tags) == 0:
            return
        self.set_type_tags(item, type_tags, platform=False)

        item["extras"] = {k: v for k, v in item["extras"].items() if v}
        item = {k: v for k, v in item.items() if v}

        # needed later for emitting platforms with the right tags
        self.stations[ifopt_id] = item
        self.station_type_tags[ifopt_id] = type_tags
        if "lat" in item and "lon" in item:
            yield item

    def parse_operator(self, r):
        op = r["businessOrganisationAbbreviationEn"].strip()
        return op if not op.startswith("Dummy") else None

    def parse_date(self, d):
        if d and not d.startswith("9999"):
            # Make sure we actually produce ISO-formatted dates.
            return datetime.date.fromisoformat(d).isoformat()
        else:
            return None

    def parse_lifecycle(self, r):
        tags = {
            "start_date": self.parse_date(r["validFrom"]),
            "end_date": self.parse_date(r["validTo"]),
        }
        return {k: v for k, v in tags.items() if v}

    def lifecycle_prefix(self, item):
        start_date = item["extras"].get("start_date", self.today)
        end_date = item["extras"].get("end_date", self.today)
        if self.today < start_date:
            return "planned:"
        elif self.today > end_date:
            return "disused:"
        else:
            return ""

    def parse_station_type(self, r, item):
        station_types = r["meansOfTransport"].split("|")
        if len(station_types) == 0:
            return []
        tags = list(PRIMARY_STATION_TAGS.get(station_types[0], []))
        for st in station_types[1:]:
            tags.extend(SECONDARY_STATION_TAGS.get(st, []))
        return tags

    # Sets the type of the station or platform, possibly with a
    # lifecycle prefix such as "planned:" or "disused:" depending
    # on "start_date" and "end_date" tags already present on item.
    def set_type_tags(self, item, tags, platform):
        extras = item["extras"]
        prefix = self.lifecycle_prefix(item)
        for key, value in tags:
            extras.setdefault(prefix + key, value)
        if platform:
            public_transport = "platform"
        elif any(key == "railway" for (key, _) in tags):
            public_transport = "station"
        else:
            public_transport = "stop_area"
        extras[prefix + "public_transport"] = public_transport

    def process_platform(self, r):
        if r["trafficPointElementType"] != "BOARDING_PLATFORM":
            return

        platform_id = r["sloid"]
        station_id = r["parentSloidServicePoint"]
        station = self.stations.get(station_id)
        station_type = self.station_type_tags.get(station_id)
        if not station or not station_type:
            return

        operator = r["servicePointBusinessOrganisationAbbreviationEn"]
        if operator.startswith("Dummy"):
            operator = ""

        item = {
            "country": station.get("country"),
            "lat": round(float(r["wgs84North"] or "0"), 8),
            "lon": round(float(r["wgs84East"] or "0"), 8),
            "ref": platform_id,
            "extras": {
                "ele:regional": round(float(r["height"] or "0"), 2),
                "official_name": self.cleanup_name(r["designationOfficial"]),
                "operator": operator,
                "ref:IFOPT": platform_id,
            },
        }
        item["extras"].update(self.parse_lifecycle(r))
        self.set_type_tags(item, station_type, platform=True)
        item["extras"] = {k: v for k, v in item["extras"].items() if v}
        item = {k: v for k, v in item.items() if v}
        if "lat" in item and "lon" in item:
            yield item

    def cleanup_name(self, name):
        return " ".join(name.split()).replace("'", "’")

    def process_zip(self, response, row_callback):
        with zipfile.ZipFile(io.BytesIO(response.body)) as zf:
            file = next(n for n in zf.namelist() if n.endswith(".csv"))
            with zf.open(file) as fp:
                content = fp.read().decode("utf-8").removeprefix("\ufeff")
                sio = io.StringIO(content)
                for rec in csv.DictReader(sio, delimiter=";"):
                    for item in row_callback(rec):
                        yield item


# Just for debugging, in the real setup this is part of the ATP framwork.
class Exporter(object):
    def __init__(self, path):
        self.out = open(path, "w")
        self.out.write('{"type":"FeatureCollection","features":[\n')
        self.first = True

    def write(self, item):
        f = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [item["lon"], item["lat"]],
            },
            "properties": {
                "country": item.get("country", ""),
                "ref": item["ref"],
            },
        }
        f["properties"].update(item["extras"])
        if not self.first:
            self.out.write(",\n")
        json.dump(f, self.out, ensure_ascii=False, sort_keys=True)
        self.first = False

    def close(self):
        self.out.write("]}\n")
        self.out.close()


if __name__ == "__main__":
    exporter = Exporter("out.geojson")
    spider = OpenTransportDataCHSpider(exporter)
    spider.start_requests()
    exporter.close()
