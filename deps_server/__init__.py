# deps_server - simple demo of Flask RESTful service.
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

"""Deps Server initialization and main application factory."""

import os

from flask import Flask

# from .db import db_core
from . import deps_app


def create_app(test_config=None):
    """The main app factory - create and initialize an app instance.

    Return: the created instance.
    """

    # Create and configure the app.
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        # DATABASE=os.path.join(app.instance_path, 'sensors.sqlite'),
    )

    if test_config is None:
        # Load the instance config, if it exists, when not testing.
        app.config.from_pyfile('config.py', silent=True)
    else:
        # Load the test config if passed in.
        app.config.from_mapping(test_config)

    # Ensure the instance folder exists.
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Initialize database module.
    # db_core.init_app(app)
    # Initialize Flask RESTful module.
    deps_app.init_rest_api(app)

    return app
