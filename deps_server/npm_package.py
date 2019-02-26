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
import aiohttp
import asyncio

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
        """Return the NPM service URL for this package."""
        return '{}/{}/{}'.format(cmn.NPM_REG_URL,
                                 self.package_name,
                                 self.__get_clean_version())

    async def fetch_deps(self, session):
        """Asynchronously fetch dependencies list for this package."""
        async with session.get(self.npm_url) as resp:
            if resp.status == cmn.HTTP_STATUS_OK:
                # got package, process its dependencies
                json = await resp.json()
                pkg_ver = json.get(cmn.NPM_DEPS_KEY)
                if pkg_ver:
                    self._deps = [Package(pkg, ver)
                                  for pkg, ver in pkg_ver.items()]
                return self._deps
            elif self.is_root:
                # failed to retrive package, if it was the root
                # package, set error status
                return DepsError(resp.status, resp.reason)
            else:
                # child package - fail silently
                return None


class NPMDepsFetcher:
    """Manage fetching all dependencies of a package asynchronously and
    recursively.
    """

    def __init__(self, package_name, version_or_tag, num_workers):

        # Keep track of processed packages so we don't fetch the same
        # package/version more than once and prevent cyclic fetches
        self._seen_pkgs = set()

        # Packages to work on
        self._pkgs_queue = None

        # Initialize queue with root package
        self._root_package = Package(
            package_name, version_or_tag, is_root=True)

        self._num_workers = num_workers

        # status != 0 means error occurred
        self._status = None

    async def _fetch_worker(self, name):
        """Coroutine for fetching dependencies of a package."""

        while True:
            # Get a package to work on out of the queue.
            pkg = await self._pkgs_queue.get()

            async with aiohttp.ClientSession() as session:
                pkg_deps = await pkg.fetch_deps(session)
                if isinstance(pkg_deps, list) and pkg_deps:
                    child_pkgs = [p for p in pkg_deps
                                  if p not in self._seen_pkgs]

                    self._seen_pkgs.update(child_pkgs)
                    for p in child_pkgs:
                        self._pkgs_queue.put_nowait(p)
                # elif isinstance(pkg_deps, int) and pkg_deps:
                elif isinstance(pkg_deps, DepsError):
                    # failed to retrive root package, set error status
                    self._status = pkg_deps

            # Notify the queue that the package has been processed.
            self._pkgs_queue.task_done()

    async def _bfs_fetch_deps(self):
        """Recursively fetch dependencies of given package/version."""

        # Packages to work on - the queue needs to be created here,
        # inside the context off the event loop.
        self._pkgs_queue = asyncio.Queue()
        self._pkgs_queue.put_nowait(self._root_package)

        # Create worker tasks to process the queue concurrently.
        tasks = [asyncio.create_task(self._fetch_worker(f'worker-{i}'))
                 for i in range(self._num_workers)]

        # Wait until the queue is fully processed.
        await self._pkgs_queue.join()

        # Cancel worker tasks
        for task in tasks:
            task.cancel()

        await asyncio.gather(*tasks, return_exceptions=True)

        # Convert to a dictionary/list tree and return result
        return Package.packages_to_tree(self._root_package)

    def fetch_all_deps(self):
        """Fetch all dependencies for the root package and return the result
        as a tree structure.
        """

        # try to get a running event loop if one exists,
        # otherwise create a new one
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()

        res = loop.run_until_complete(self._bfs_fetch_deps())
        loop.close()
        if self._status:
            # raise DepsError(self._status, "Not found")
            raise self._status
        return res
