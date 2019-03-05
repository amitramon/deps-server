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
from .npm_package import Package, DepsError


class PackageFetcher(Package):
    """NPM Package fetcher.

    Add an asyncio fetching coroutine to the Package class.
    """

    async def fetch_deps(self, session):
        """Asynchronously fetch dependencies list for this package."""
        async with session.get(self.npm_url) as resp:
            if resp.status == cmn.HTTP_STATUS_OK:
                # got package, process its dependencies
                json = await resp.json()
                pkg_ver = json.get(cmn.NPM_DEPS_KEY)
                if pkg_ver:
                    self._deps = [PackageFetcher(pkg, ver)
                                  for pkg, ver in pkg_ver.items()]
                return self._deps
            elif self.is_root:
                # failed to retrive package, if it was the root
                # package, set error status
                raise DepsError(resp.status, resp.reason)
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
        self._root_package = PackageFetcher(package_name,
                                            version_or_tag,
                                            is_root=True)

        self._num_workers = num_workers

    def _cleanup(self):
        """Clear the packages queue"""
        try:
            while True:
                self._pkgs_queue.get_nowait()
                try:
                    self._pkgs_queue.task_done()
                except ValueError:
                    pass
        except asyncio.QueueEmpty:
            pass

    async def _fetch_pkg_deps(self, pkg):
        """Fetch dependencies for pkg, associate them with pkg and add them to
        the packages queue
        """
        async with aiohttp.ClientSession() as session:
            pkg_deps = await pkg.fetch_deps(session)

            if pkg_deps:
                child_pkgs = [p for p in pkg_deps
                              if p not in self._seen_pkgs]

                # Add the new dependencies pacages to the seen
                # packages and to the processing queue
                self._seen_pkgs.update(child_pkgs)
                for p in child_pkgs:
                    self._pkgs_queue.put_nowait(p)

    async def _fetch_worker(self, name):
        """Fetch and process dependencies of a package."""

        while True:
            # Get a package to work on out of the queue.
            pkg = await self._pkgs_queue.get()
            try:
                await self._fetch_pkg_deps(pkg)
            except DepsError:
                # clear queue, this will release the wait on the queue
                # and subsequently cancell the fetch tasks
                self._cleanup()
                raise
            finally:
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

        # wait until all tasks are finished
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for res in results:
            if isinstance(res, DepsError):
                raise res

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

        try:
            res = loop.run_until_complete(self._bfs_fetch_deps())
        finally:
            loop.close()

        return res
