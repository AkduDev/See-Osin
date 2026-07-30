"""See - Phone Number OSINT Tool"""

from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("see-osint")
except PackageNotFoundError:
    __version__ = "0.1.0-dev"
