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

import collections
import csv
import datetime
import io
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

    def start_requests(self):
        url_pattern = "https://opentransportdata.swiss/en/dataset/%s/permalink"
        # yield scrapy.Request(url, callback=self.extract_service_points)
        # yield scrapy.Request(url, callback=self.extract_traffic_points)
        self.download(
            url_pattern % "service-points-full", callback=self.extract_service_points
        )
        self.download(
            url_pattern % "traffic-points-full", callback=self.extract_traffic_points
        )

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
        with open(zip_path, "rb") as fp:
            response = FakeScrapyResponse(fp.read())
            for item in callback(response):
                print(item)

    def extract_service_points(self, response):
        return self.process_zip(response, self.process_service_point)

    def extract_traffic_points(self, response):
        return self.process_zip(response, self.process_traffic_point)

    def process_service_point(self, r):
        if r.get("status") != "VALIDATED":
            return
        item = {
            "lat": round(float(r["wgs84North"] or "0"), 8),
            "lon": round(float(r["wgs84East"] or "0"), 8),
            "country": r["isoCountryCode"].upper(),
            "ref": r["sloid"],
            "extras": {
                "ele:regional": round(float(r["height"] or "0"), 2),
                "official_name": self.cleanup_name(r["designationOfficial"]),
                "operator": self.parse_operator(r),
                "ref:IFOPT": r["sloid"],
            },
        }
        item["extras"].update(self.parse_lifecycle(r))
        if not self.parse_type(r, item):
            return
        item["extras"] = {k: v for k, v in item["extras"].items() if v}
        item = {k: v for k, v in item.items() if v}
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

    def parse_type(self, r, item):
        stop_types = r["meansOfTransport"].split("|")
        if len(stop_types) == 0:
            return False
        tags = list(PRIMARY_STATION_TAGS.get(stop_types[0], []))
        for st in stop_types[1:]:
            tags.extend(SECONDARY_STATION_TAGS.get(st, []))
        if len(tags) == 0:
            return False

        # Primary mode of transportation, possibly with lifecycle prefix.
        key, value = tags[0]
        today = datetime.date.today().isoformat()
        start_date = item["extras"].get("start_date", today)
        end_date = item["extras"].get("end_date", today)
        if today < start_date:
            key = "planned:" + key
        elif today > end_date:
            key = "disused:" + key
        item["extras"][key] = value

        # Secondary keys. It seems the upstream data model adds a new
        # station, and marks the old one as disused, if the modes of
        # transportation change.
        for key, value in tags[1:]:
            item["extras"].setdefault(key, value)
        return True

    def process_traffic_point(self, r):
        if r["trafficPointElementType"] != "BOARDING_PLATFORM":
            return
        item = {
            "lat": round(float(r["wgs84North"] or "0"), 8),
            "lon": round(float(r["wgs84East"] or "0"), 8),
            "ref": r["sloid"],
            "extras": {
                "ele:regional": round(float(r["height"] or "0"), 2),
                "official_name": self.cleanup_name(r["designationOfficial"]),
                "public_transport": "platform",
                "ref:IFOPT": r["sloid"],
            },
        }
        item["extras"] = {k: v for k, v in item["extras"].items() if v}
        item = {k: v for k, v in item.items() if v}
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


if __name__ == "__main__":
    spider = OpenTransportDataCHSpider()
    spider.start_requests()
