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

import argparse, codecs, collections, itertools, json
import os, tempfile, urllib
from datetime import datetime

try:  # Python 3
    import http.client, urllib.parse, urllib.request
    urlopen = urllib.request.urlopen
    urlquote = urllib.parse.quote_plus
except ImportError:  # Python 2
    import httplib
    urlopen = urllib.urlopen
    urlquote = urllib.quote_plus


REGIONS = {
    # ISO 3166-1/2: 'CH' for Switzerland; 'DE-BY' for Bavaria
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
    for layer, region in itertools.product(LAYERS.keys(), REGIONS.keys()):
        process(layer, region, output_dir=args.output_dir)


def process(layer, region, output_dir):
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)
    query = build_overpass_query(layer, region)
    url = OVERPASS_ENDPOINT + '?data=' + urlquote(query, safe='.:;/()')
    fetch_start = datetime.utcnow()
    content, fetch_status = fetch_url(url)
    now = datetime.utcnow()
    logrec = {
        'timestamp': now.isoformat() + 'Z',  # 'Z' = UTC as per ISO 8601
        'layer': layer, 'region': region,
        'fetch_duration_seconds': (now - fetch_start).total_seconds(),
        'fetch_http_status_code': fetch_status,
    }
    status = 'fail'
    if fetch_status == 200:
        geojson = overpass_to_geojson(json.loads(content))
        logrec.update(summarize_stats(geojson))
        # Only use results when Overpass actually returned any features.
        # Sometimes, the API returns empty results in an HTTP reply
        # with "200 OK" status; let's work around this.
        if len(geojson['features']) > 0:
            geojson_blob = format_json(geojson).encode('utf-8')
            logrec['output_bytes'] = len(geojson_blob)
            filepath = os.path.join(output_dir,
                                    'osm-%s-%s.geojson' % (layer, region))
            changed = replace_file_content(filepath, geojson_blob)
            logrec['changed'] = 'true' if changed else 'false'
            status = 'ok'
        else:
            status = 'fail_nofeatures'
    logrec['status'] = status
    append_logrecord(logrec, os.path.join(output_dir, 'fetch_layers.log'))


def summarize_stats(fcoll):
    """Compute summary statistics for a GeoJSON feature collection."""
    assert fcoll['type'] == 'FeatureCollection'
    geometry_type = \
        collections.Counter([f['geometry']['type'] for f in fcoll['features']])
    tags = collections.Counter()
    for f in fcoll['features']:
        tags.update(f['properties'].keys())
    return {
        'geometry_type_most_common': dict(geometry_type.most_common(1000)),
        'tags_most_common': dict(tags.most_common(1000)),
        'tags_total': len(tags),
    }


def fetch_url(url):
    #with open('cached-results.json', 'rb') as f: return (f.read(), 200)
    try:
        connection = urlopen(url)
        content = connection.read()
        connection.close()
        return (content, connection.code)
    except:
        return (b'', 520)  # unofficial code (eg. Cloudflare) for network errs
    #with open('cached-results.json', 'wb') as f: f.write(content)


def replace_file_content(filepath, content):
    """Atomially replace filepath by new content if content is new."""
    assert isinstance(content, bytes)
    # If content has not changed, we do not touch the existing file
    # so its timestamp stays the same.
    if os.path.exists(filepath):
        with open(filepath, 'rb') as old_file:
            old_content = old_file.read()
        if content == old_content:
            return False  # no change
    basename = os.path.basename(filepath)
    suffix = basename.rsplit('.', 1)[-1] if '.' in basename else '.tmp'
    tmpfd, tmpname = tempfile.mkstemp(dir=os.path.dirname(filepath),
                                      prefix='tmp-', suffix=suffix)
    with os.fdopen(tmpfd, 'wb') as out:
         out.write(content)
    os.rename(tmpname, filepath)
    return True  # content has changed


def append_logrecord(rec, filepath):
    with open(filepath, 'ab') as f:
        f.write(format_json(rec).replace('\n', ' ').encode('utf-8'))
        f.write(b'\n')
        f.flush()
        os.fsync(f.fileno())


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
                'coordinates': lonlat(node),
            },
            'properties': tags,
        })
    for way in filter(lambda e: e['type'] == 'way', elements):
        geometry = way['geometry']
        tags = dict(way['tags'])
        tags['.id'] = 'W%s' % way['id']
        closed = (geometry[0] == geometry[-1])
        coords = [lonlat(p) for p in geometry]
        if closed:
            coords = fix_ring_direction('outer', coords)
        features.append({
            'type': 'Feature',
            'geometry': {
                'type': 'Polygon' if closed else 'LineString',
                'coordinates': [coords] if closed else coords,
            },
            'properties': tags,
        })
    for rel in filter(lambda e: e['type'] == 'relation', elements):
        features.append(overpass_relation_to_geojson(rel))
    return {
        'type': 'FeatureCollection',
        'features': features
    }


def overpass_relation_to_geojson(rel):
    tags = dict(rel['tags'])
    tags['.id'] = 'R%s' % rel['id']
    members = rel['members']
    outer = [m for m in members if m['role'] == 'outer' and m['type'] == 'way']
    if len(outer) != 1:  # we don't handle multipolygons etc., return a point
        bounds = rel['bounds']
        minlon, maxlon = bounds['minlon'], bounds['maxlon']
        minlat, maxlat = bounds['minlat'], bounds['maxlat']
        lon = minlon + (maxlon - minlon) / 2
        lat = minlat + (maxlat - minlat) / 2
        return {
            'type': 'Feature',
            'geometry': {
                'type': 'Point',
                'coordinates': [lon, lat],
            },
            'properties': tags,
        }
    assert len(outer) == 1, tags
    outer_ring = [lonlat(p) for p in outer[0]['geometry']]
    rings = [fix_ring_direction('outer', outer_ring)]
    for m in members:
        if m['role'] == 'inner' and m['type'] == 'way':
            inner_ring = [lonlat(p) for p in m['geometry']]
            rings.append(fix_ring_direction('inner', inner_ring))
    return {
        'type': 'Feature',
        'geometry': {
            'type': 'Polygon',
            'coordinates': rings,
         },
        'properties': tags,
    }


def lonlat(p):
    return [p['lon'], p['lat']]


def fix_ring_direction(direction, coords):
    # https://stackoverflow.com/questions/1165647
    assert direction in {'outer', 'inner'}
    assert coords[0] == coords[-1], 'ring must be closed'
    total = 0
    for i in range(len(coords) - 1):
        (Px, Py), (Qx, Qy) = coords[i], coords[i + 1]
        total += (Qx - Px) * (Qy + Py)
    if ((direction == 'outer' and total > 0) or
        (direction == 'inner' and total <= 0)):
        coords.reverse()
    return coords


def format_json(j):
    return json.dumps(j, ensure_ascii=False,
                      sort_keys=True, separators=(',', ':'))


if __name__ == '__main__':
    main()
