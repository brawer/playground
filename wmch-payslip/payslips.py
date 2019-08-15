#!/usr/bin/python3
# -*- mode: python; coding: utf-8 -*-
#
# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2019 Sascha Brawer <sascha@brawer.ch>

import csv
import datetime
import collections
import re
import sqlite3
import time
from io import StringIO


DATABASE_PATH = '/etc/payslips/payslip.db'


# PostFinance allows for arbitrary reference numbers without any constraints.
# We use a statically assigned prefix of 12 digits of our own choosing,
# so that other processes who generate reference numbers will be unlikely
# to hand out conflicting numbers.
REFNO_PREFIX = '990001997812'
assert len(REFNO_PREFIX) == 12


def app(environ, start_response):
    path = environ['PATH_INFO']
    match = re.match(
        r'^.*?/api/v1/merchants/wik-i7yylr/campaigns/([a-zA-Z0-9\-]+)/'
        r'payingin-slip-refno/fetch$', path)
    if match is not None:
        return create_payslip(environ, start_response, match.group(1))

    if path.endswith('/payslips.csv'):
        return handle_payslips_csv(environ, start_response)

    status = '200 OK'
    output = b'Hello World!\n'
    response_headers = [('Content-Type', 'text/plain'),
                        ('Content-Length', str(len(output)))]
    start_response(status, response_headers)
    return [output]


def create_payslip(env, start_response, campaign_id):
    if env['REQUEST_METHOD'] != 'POST':
        return send_error_method_not_allowed(env, start_response, 'POST')
    with PayslipDB(DATABASE_PATH) as db:
        payslip = db.create_payslip(campaign_id=campaign_id)
    status = '200 OK'
    # It is intentional that the output contains no trailing newline character.
    # The RaiseNow.ch site (which is the client to this server) does not
    # strip off any whitespace; RaiseNow breaks if we return a newline.
    output = payslip.payslip_id.encode('utf-8')
    response_headers = [('Content-Type', 'text/plain;charset=utf-8'),
                        ('Content-Length', str(len(output)))]
    start_response(status, response_headers)
    return [output]


def handle_payslips_csv(env, start_response):
    method = env['REQUEST_METHOD']
    if method in ('GET', 'HEAD'):
        return get_payslips_csv(env, start_response)
    elif method == 'PUT':
        return put_payslips_csv(env, start_response)
    else:
        return send_error_method_not_allowed(env, start_response,
                                             'GET, HEAD, PUT')


def get_payslips_csv(env, start_response):
    out = StringIO()
    out.write('Payslip,Campaign,Timestamp\n')
    with PayslipDB(DATABASE_PATH) as db:
        for p in db.get_payslips():
            # All vlues are in [A-Za-z0-9\-:.]; no need to escape them.
            out.write('%s,%s,%s\n' %
                      (p.payslip_id, p.campaign_id, p.timestamp))
    output = out.getvalue().encode('utf-8')
    start_response('200 OK', [('Content-Type', 'text/csv;charset=utf-8'),
                              ('Content-Length', str(len(output)))])
    return [output] if env['REQUEST_METHOD'] != 'HEAD' else []


def put_payslips_csv(env, start_response):
    payslips = []
    with StringIO() as buf:
        for line in env['wsgi.input']:
            buf.write(line.decode('utf-8'))
        body = buf.getvalue()
    dialect = csv.Sniffer().sniff(body)
    line_number = 1  # Not 0, because CSV header is at line 1.
    for rec in csv.DictReader(body.splitlines(), dialect=dialect):
        line_number += 1
        payslip_id = rec['Payslip'].replace(' ', '')
        if re.match(r'^\d{27}$', payslip_id) is None:
            return send_error_bad_request(
                env, start_response, 'Bad Payslip on line %d' % line_number)
        campaign_id = rec['Campaign'].strip()
        if re.match(r'^[A-Za-z0-9\-]+$', campaign_id) is None:
            return send_error_bad_request(
                env, start_response, 'Bad Campaign on line %d' % line_number)
        timestamp = rec['Timestamp'].strip()
        if re.match(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z$',
                    timestamp) is None:
            return send_error_bad_request(
                env, start_response, 'Bad Timestamp on line %d' % line_number)
        p = Payslip(payslip_id=payslip_id, campaign_id=campaign_id,
                    timestamp=timestamp)
        payslips.append(p)
    with PayslipDB(DATABASE_PATH) as db:
        db.put_payslips(payslips)
    start_response('204 No Content', [])
    return []


def send_error_bad_request(env, start_response, msg):
    status = '400 Bad Request'
    output = ('400 Bad Request: %s\n' % msg).encode('utf-8')
    start_response(status, [('Content-Type', 'text/plain;charset=utf-8'),
                            ('Content-Length', str(len(output)))])
    return [output]


def send_error_method_not_allowed(env, start_response, allow):
    status = '405 Method Not Allowed'
    output = ('405 Method Not Allowed; use %s\n' % allow).encode('utf-8')
    start_response(status, [('Content-Type', 'text/plain;charset=utf-8'),
                            ('Content-Length', str(len(output))),
                            ('Allow', allow)])
    return [output]


Payslip = collections.namedtuple('Payslip', 'payslip_id campaign_id timestamp')


class PayslipDB(object):
    def __init__(self, filepath):
        self.db = sqlite3.connect(filepath)
        c = self.db.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS Payslips (
            sequence_number INTEGER PRIMARY KEY AUTOINCREMENT,
            payslip_id TEXT,
            campaign_id TEXT,
            timestamp TEXT);''')
        self.db.commit()
        del c

    def __enter__(self):
        return self

    def __exit__(self, _extype, _exvalue, _traceback):
        del self.db

    def create_payslip(self, campaign_id, timestamp=None):
        if timestamp is None:
            t = datetime.datetime.utcfromtimestamp(time.time())
            timestamp = t.isoformat('T') + 'Z'
        c = self.db.cursor()
        c.execute(
            'INSERT INTO Payslips (campaign_id, timestamp) VALUES (?, ?);',
            (campaign_id, timestamp))
        c.execute('SELECT last_insert_rowid();')
        seqno = c.fetchone()[0]
        payslip_id = self._format_reference_number(seqno)
        c.execute(
            '''UPDATE Payslips SET payslip_id = ? 
            WHERE sequence_number = ?;''',
            (payslip_id, seqno))
        payslip = Payslip(payslip_id=payslip_id, campaign_id=campaign_id,
                          timestamp=timestamp)
        self.db.commit()
        del c
        return payslip

    def get_payslips(self):
        c = self.db.cursor()
        for row in c.execute(
            '''SELECT payslip_id, campaign_id, timestamp FROM Payslips
            ORDER BY payslip_id;'''):
            yield Payslip(payslip_id=row[0], campaign_id=row[1],
                          timestamp=row[2])
        del c

    def put_payslips(self, payslips):
        c = self.db.cursor()
        c.execute('DELETE FROM Payslips;')
        for p in payslips:
            seqno = int(p.payslip_id[12:-1])
            c.execute(
                'INSERT INTO Payslips '
                '(sequence_number, payslip_id, campaign_id, timestamp) '
                'VALUES (?, ?, ?, ?);',
                (seqno, p.payslip_id, p.campaign_id, p.timestamp))
        self.db.commit()
        del c

    def _format_reference_number(self, seqno):
        digits = REFNO_PREFIX + '%014d' % seqno
        assert len(digits) == 26, 'should have 26 digits: %s' % digits
        table, carry = (0, 9, 4, 6, 8, 2, 7, 1, 3, 5), 0
        for n in digits:
            carry = table[(carry + int(n)) % 10]
        checksum = (10 - carry) % 10
        return digits + str(checksum)

