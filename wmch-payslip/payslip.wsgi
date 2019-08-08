#!/usr/bin/python3
# -*- mode: python; coding: utf-8 -*-
#
# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2019 Sascha Brawer <sascha@brawer.ch>

import datetime
import collections
import re
import sqlite3
import time
from io import StringIO


DATABASE_PATH = './payslip.db'


# TODO: Ask PostFinance for the actual number
REFNO_PREFIX = '990001'
assert len(REFNO_PREFIX) == 6

REFNO_NAMESPACE = '997812'  # Assigned by ourselves, follows REFNO_PREFIX.
assert len(REFNO_NAMESPACE) == 6


def application(environ, start_response):
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
    output = (payslip.payslip_id + '\n').encode('utf-8')
    response_headers = [('Content-Type', 'text/plain;charset=utf-8'),
                        ('Content-Length', str(len(output)))]
    start_response(status, response_headers)
    return [output]


def handle_payslips_csv(env, start_response):
    method = env['REQUEST_METHOD']
    # TODO: Handle PUT to replace current databse contents.
    if method in ('GET', 'HEAD'):
        return get_payslips_csv(env, start_response)
    else:
        return send_error_method_not_allowed(env, start_response,
                                             'GET, HEAD')

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


def send_error_method_not_allowed(env, start_response, allow):
    status = '405 Method Not Allowed'
    output = ('405 Method Not Allowed; use %s\n' % allow).encode('utf-8')
    start_response(status, [('Content-Type', 'text/plain;charset=utf-8'),
                            ('Content-Length', str(len(output))),
                            ('Allow', allow)])
    return [output] if env['REQUEST_METHOD'] != 'HEAD' else []


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

    def _format_reference_number(self, seqno):
        digits = REFNO_PREFIX + REFNO_NAMESPACE + '%014d' % seqno
        assert len(digits) == 26, 'should have 26 digits: %s' % digits
        table, carry = (0, 9, 4, 6, 8, 2, 7, 1, 3, 5), 0
        for n in digits:
            carry = table[(carry + int(n)) % 10]
        checksum = (10 - carry) % 10
        return digits + str(checksum)

