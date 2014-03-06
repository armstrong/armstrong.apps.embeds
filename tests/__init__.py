from .models import *
from .backends import *
from .admin import *
from .fields import *
from .forms import *
from .mixins import *
from .templatetags import *

# Silence logging during tests
from armstrong.apps.embeds import logger
try:
    from logging import NullHandler
except ImportError:  # Python 2.6 support # pragma: no cover
    from logging import Handler

    class NullHandler(Handler):
        def emit(self, record):
            pass

logger.addHandler(NullHandler())
