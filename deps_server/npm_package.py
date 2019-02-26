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

"""NPM Package

Describes the structure and methods of an NPM package.
"""

from . import commons as cmn


class DepsError(Exception):
    """Exception thrown on data errors."""

    def __init__(self, err_code, message):
        super().__init__(message)
        self.err_code = err_code


class Package:
    """NPM Package manager."""

    @staticmethod
    def packages_to_tree(pkg):
        """Convert the dependencies tree structure into a dictionary/lists
        tree structure.
        """
        d = {}
        d[cmn.PKG_NAME_KEY] = pkg.package_name
        d[cmn.VERSION_KEY] = pkg.version_or_tag
        if pkg.has_deps:
            # recursively add subtrees
            d[cmn.DEPS_KEY] = [Package.packages_to_tree(p) for p in pkg]

        return d

    def __init__(self, package_name, version_or_tag, is_root=False):
        self.package_name = package_name
        self.version_or_tag = version_or_tag
        # Mark the root tree, since failing to fetch it is a fatal
        # error
        self.is_root = is_root
        self._deps = None

    # TODO: a hack - currently only plain version strings (i.e. no
    # ranges or other patters) are handled correctly. this allow to
    # also handle simple major/minor, although it might give
    # inaccurate results.
    def __get_clean_version(self):
        return (self.version_or_tag[1:]
                if self.version_or_tag[0] in ('^', '~')
                else self.version_or_tag)

    def __str__(self):
        return self.package_name + '::' + self.version_or_tag

    # The following methods handle this package's dependencies list,
    # and provide a "list" interface to this instance
    def append_dep(self, p):
        """Append a single dependency to this package."""
        self._deps.append(p)

    def extend_deps(self, deps):
        """Extend the dependencie list of this package with the given list."""
        self._deps.extend(deps)

    def __getitem__(self, i):
        """Provide array index access to this package dependencies."""
        return self._deps[i]

    @property
    def has_deps(self):
        return self._deps and len(self._deps) > 0

    @property
    def npm_url(self):
        """Return the NPM service URL of this package."""
        return '{}/{}/{}'.format(cmn.NPM_REG_URL,
                                 self.package_name,
                                 self.__get_clean_version())
