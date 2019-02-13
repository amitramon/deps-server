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

from collections import deque

import requests

from . import commons as cmn


class DepsError(Exception):
    """Exception thrown on data errors."""

    def __init__(self, err_code, message):
        super().__init__(message)
        self.err_code = err_code


class Package:
    """NPM Package manager."""

    def __init__(self, package_name, version_or_tag, is_root=False):
        self.package_name = package_name
        self.version_or_tag = version_or_tag
        self.is_root = is_root

    # TODO: a hack - currently only plain version strings (i.e. no
    # ranges or other patters) are handled correctly. this allow to
    # also handle simple major/minor, although it might give
    # inaccurate results.
    def __get_clean_version(self):
        return (self.version_or_tag[1:]
                if self.version_or_tag[0] in ('^', '~')
                else self.version_or_tag)

    @property
    def npm_url(self):

        return '{}/{}/{}'.format(cmn.NPM_REG_URL,
                                 self.package_name,
                                 self.__get_clean_version())

    def fetch_deps(self):

        response = requests.get(self.npm_url)

        if response.ok:
            return response.json().get('dependencies')
        elif self.is_root:
            raise DepsError(response.status_code, response.reason)
        else:
            # child package - fail silently
            return None


def bfs_fetch_deps(package_name, version_or_tag):
    """Recursively fetch dependencies of given package/version."""

    # keep track on processed packages so we don't fetch the same
    # package/version more than once and prevent cyclic fetches
    seen_pkgs = set()

    # packages to work on
    pkgs_queue = deque()

    # initialize queue with root package
    pkgs_queue.append(Package(package_name,
                              version_or_tag,
                              is_root=True))

    while pkgs_queue:
        pkg = pkgs_queue.popleft()
        deps = pkg.fetch_deps()
        if deps:
            child_pkgs = [p for p in deps.items() if p not in seen_pkgs]
            seen_pkgs.update(child_pkgs)
            pkgs_queue.extend([Package(*p) for p in child_pkgs])

    return {pkg: ver for (pkg, ver) in seen_pkgs}
