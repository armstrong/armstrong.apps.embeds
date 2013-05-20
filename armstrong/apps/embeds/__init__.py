from pkgutil import extend_path
__path__ = extend_path(__path__, __name__)

# Define a logger for this component
import logging
logger = logging.getLogger(__name__)
