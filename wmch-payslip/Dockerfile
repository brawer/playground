# SPDX-FileCopyrightText: 2019 Sascha Brawer <sascha@brawer.ch>
# SPDX-License-Identifier: MIT
#
# For running the server on a development machine:
# $ docker build -t payslip . && docker run -it --rm -p 8000:80 payslip
#
# To create a new payslip reference number (do this on the host machine):
# $ curl -X POST http://localhost:8000/path/to/payslips/api/v1/merchants/wik-i7yylr/campaigns/Campaign789/payingin-slip-refno/fetch
#
# To retrieve the current list of ever-issued payslips (on the host machine):
# $ curl http://localhost:8000/path/to/payslips/payslips.csv -o payslips.csv

FROM grahamdumpleton/mod-wsgi-docker:python-3.5-onbuild
CMD [ "payslip.wsgi" ]
EXPOSE 80
