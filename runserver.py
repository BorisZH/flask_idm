"""
This script runs the AutoExpManager application using a development server.
"""

from os import environ
from idm import app
import optparse
# from idm.service import check_configuration


if __name__ == '__main__':
    deflt_port = 4444
    parser = optparse.OptionParser()
    parser.add_option('-P',
                      '--port',
                      help="Port for app. Default: {}".format(deflt_port),
                      default=deflt_port)

    options, _ = parser.parse_args()

    HOST = environ.get('SERVER_HOST', '0.0.0.0')
    try:
        PORT = int(environ.get('SERVER_PORT',''))
    except ValueError:
        PORT = options.port
    # check_configuration()
    app.config.from_pyfile('configs\\config.py')
    app.run(HOST, PORT)
