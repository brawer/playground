#!/usr/bin/python3
#
# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: 2019 Sascha Brawer <sascha@brawer.ch>

def application(environ, start_response):
    status = '200 OK'
    output = b'Hello World!\n'
    response_headers = [('Content-Type', 'text/plain'),
                        ('Content-Length', str(len(output)))]
    start_response(status, response_headers)
    return [output]
