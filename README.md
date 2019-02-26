# Deps Server

The Deps Server is a simple REST Service for recursively fetching NPM
package dependencies.

It has a single API:

    /<package_name>/<version_or_tag>/

The service uses Python's asyncio for concurrently fetching
dependencies. The number of worker coroutines can be set in the
`commons.py` file.

## Requirements

The server was built and tested for Python 3. The `requirements.txt`
file in the root directory of the installation describes the required
Python modules.

## Building and Running a Docker Container

The system is ready for packing it in a Docker container. To build a
container run the following command from `<root-dir>`:

    $ docker-compose build

You will then be able to run it with:

    $ docker-compose up

The system's default configuration maps the service's port to port
*8080* on the host.

## Running the Server Locally

The server comes with two shell scripts for running it, one for
running it in development mode and one for production mode. Both
scripts need to be run from the parent directory of the
`deps_server` directory (which contains these scripts).

Notes that these scripts assume the existing of a virtual environment
with the required modules installed.

In the following sections it is assumed that the system is installed
in a directory `<root-dir>`.

### Running in Development Mode

Use the command

    $ ./bin/run_deps_server_dev

The virtual environment should be `<root-dir>/venv_dev`.

### Testing Production Mode

In production mode the system uses the **Waitress WSGI** server. You can
run it locally in that mode for testing the configuration.

You will first have to create a virtual environment
`<root-dir>/venv`, and install in it the packages listed in the
`requirements.txt` file.

Then, from `<root-dir>`, run the command

    $ ./bin/run_deps_server

The server will start on port 8080.

## License

This project is released under GNU General Public License v3.0.
