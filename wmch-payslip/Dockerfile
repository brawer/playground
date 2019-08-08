# SPDX-FileCopyrightText: 2019 Sascha Brawer <sascha@brawer.ch>
# SPDX-License-Identifier: MIT

# For developing the app:
#
# $ docker build -t payslip .
# $ docker run -it --rm -p 8000:80 --name payslip payslip

FROM grahamdumpleton/mod-wsgi-docker:python-3.5-onbuild
CMD [ "payslip.wsgi" ]
EXPOSE 80
