# SPDX-FileCopyrightText: 2019 Sascha Brawer <sascha@brawer.ch>
# SPDX-License-Identifier: MIT
#
# For running the server on a development machine:
# $ mkdir -p /tmp/payslips
# $ docker build -t payslips . && docker run -it --rm --mount type=bind,source=/tmp/payslips,target=/etc/payslips payslips -p 8000:8000 payslips
#
# To create a new payslip reference number (either on the host machine or inside the Docker VM):
# $ curl -X POST http://localhost:8000/path/to/payslips/api/v1/merchants/wik-i7yylr/campaigns/Campaign789/payingin-slip-refno/fetch
#
# To retrieve the current list of ever-issued payslips (either on the host machine or inside the Docker VM):
# $ curl http://localhost:8000/path/to/payslips/payslips.csv -o payslips.csv
#
# To replace the internal database (either on the host machine or inside the Docker VM):
# $ curl http://localhost:8000/path/to/payslips/payslips.csv --upload-file payslips.csv

FROM python:3.7.4-alpine3.10
WORKDIR /app
COPY requirements.txt *.py /app/
RUN pip install -r requirements.txt
RUN mkdir -p /etc/payslips

CMD [ "gunicorn", "-w2", "-b:8000", "payslips:app" ]
EXPOSE 8000
