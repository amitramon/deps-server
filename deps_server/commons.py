# deps_server - simple demo of NPM dependencies fetcher Flask RESTful
# service.
#
# Copyright (C) 2019 Amit Ramon <amit.ramon@riseup.net>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""Constants and variables common to Deps Server modules."""

# Constants used for describing data key names (in REST requests and
# in JSON data).
PKG_NAME_KEY = 'name'
VERSION_KEY = 'version'
DEPS_KEY = 'dependencies'
# TIMESTAMP_KEY = 'timestamp'

HTTP_STATUS_OK = 200
NPM_REG_URL = 'https://registry.npmjs.org'
