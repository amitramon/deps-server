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

"""NPM Dependencies Fetcher Server REST API.

Includes URL routing defintions and request handling rutines.
"""

# from flask_restful import reqparse, abort, Api, Resource
from flask_restful import abort, Api, Resource

from . import commons as cmn
from . npm_package import bfs_fetch_deps, DepsError


def error_abort(func):
    """Decorator for handling excepions thrown by data access methods."""

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except DepsError as e:
            abort(e.err_code, message=str(e))
        except Exception as e:
            abort(500, message=f'An error occurred: {str(e)}')

    return wrapper


class DepsFetcher(Resource):
    """REST API handler."""

    @error_abort
    def get(self, package_name, version_or_tag):
        """Get all dependencies for the given package and version."""

        deps = bfs_fetch_deps(package_name, version_or_tag)

        return {cmn.PKG_NAME_KEY: package_name,
                cmn.VERSION_KEY: version_or_tag,
                cmn.DEPS_KEY: deps}


def init_rest_api(app):
    """Initialize Flask restful and set up the URL routing rules."""

    api = Api(app, catch_all_404s=True)

    # Get dependencies.
    api.add_resource(DepsFetcher, '/<package_name>/<version_or_tag>/')
