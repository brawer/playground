# Copyright 2019 by Sascha Brawer. Licensed under the MIT license.
# SPDX-License-Identifier: MIT
#
# Tool for fetching layers of notable features from OpenStreetMap.
# This will be used for a hackathon in May 2019 about castles in Switzerland,
# organized in collaboration with Wikimedia Foundation Switzerland,
# whose goal it is to improve Swiss castles in Wikipedia. The tool
# can be extended to handle additional layers and regions.
#
# The program sends a query to the OSM Overpass API and formats the result
# in GeoJSON format. The resulting files are written into a place accessible
# to a webserver running on the same machine, so that clients can access them.
# Obviously, this simple approach will not work for layers that have lots
# features, but for the few hundred castles in Switzerland, it should do.
#
# This tool should be run as a cron job, eg. once per hour or so. Invocation:
# $ python fetch_layers.py --output_path=/path/to/public_www_directory

from __future__ import print_function, unicode_literals
import argparse, codecs, itertools, json, logging, os, tempfile, time, urllib

try:  # Python 3
    import http.client, urllib.parse, urllib.request
    urlopen = urllib.request.urlopen
    urlquote = urllib.parse.quote_plus
except ImportError:  # Python 2
    import httplib
    urlopen = urllib.urlopen
    urlquote = urllib.quote_plus


REGIONS = {
    'CH':  (45.6, 5.4, 47.99, 11.2),
}

LAYERS = {
    'castles': 'historic=castle',
}

OVERPASS_ENDPOINT = 'http://overpass-api.de/api/interpreter'


def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument('--output_dir',
                           help='path to directory for storing output files')
    args = argparser.parse_args()
    path = args.output_dir
    for layer, region in itertools.product(LAYERS.keys(), REGIONS.keys()):
        query = build_overpass_query(layer, region)
        url = OVERPASS_ENDPOINT + '?data=' + urlquote(query, safe='.:;/()')
        fetch_start = time.time()
        content, fetch_status = fetch(url)
        fetch_duration_seconds = time.time() - fetch_start
        if fetch_status == 200:
            geojson = overpass_to_geojson(json.loads(content))
            geojson_str = json.dumps(geojson, ensure_ascii=False,
                                     sort_keys=True, separators=(',', ':'))
            # we replace the file atomically, to never serve partial content
            tmpfd, tmpname = tempfile.mkstemp(dir=path, suffix='.geojson')
            with os.fdopen(tmpfd, 'wb') as out:
                out.write(geojson_str.encode('utf-8'))
            os.rename(tmpname,
                      os.path.join(path, '%s-%s.geojson' % (layer, region)))
            logging.info(
                'Fetch OK; layer=%s, region=%s, fetch_duration_seconds=%s' %
                (layer, region, fetch_duration_seconds))
        else:
            logging.error(
                'Fetch failed; layer=%s, region=%s, fetch_status=%s' %
                (layer, region, fetch_status))


def fetch(url):
    connection = urlopen(url)
    content = connection.read()
    connection.close()
    return (content, connection.code)


def build_overpass_query(layer, region):
    coverage = '(%s,%s,%s,%s)' % REGIONS[region]
    tags = LAYERS[layer]
    query_pattern = \
        '[out:json][timeout:25];nwr[%(tags)s]%(coverage)s;out geom;'
    query = query_pattern % {'coverage': coverage, 'tags': tags}
    return query


def overpass_to_geojson(op):
    elements = op['elements']
    features = []
    for node in filter(lambda e: e['type'] == 'node', elements):
        tags = dict(node['tags'])
        tags['.id'] = 'N%s' % node['id']
        features.append({
            'type': 'Feature',
            'geometry': {
                'type': 'Point',
                'coordinates': [node['lon'], node['lat']],
            },
            'properties': tags,
        })
    for way in filter(lambda e: e['type'] == 'way', elements):
        geometry = way['geometry']
        tags = dict(way['tags'])
        tags['.id'] = 'W%s' % way['id']
        closed = (geometry[0] == geometry[-1])
        coords = [[p['lon'], p['lat']] for p in geometry]
        features.append({
            'type': 'Feature',
            'geometry': {
                'type': 'Polygon' if closed else 'LineString',
                'coordinates': [coords] if closed else coords,
            },
            'properties': tags,
        })
    for rel in filter(lambda e: e['type'] == 'relation', elements):
        tags = dict(rel['tags'])
        tags['.id'] = 'R%s' % rel['id']
        pass  # TODO
    return {
        'type': 'FeatureCollection',
        'features': features
    }


if __name__ == '__main__':
    main()
