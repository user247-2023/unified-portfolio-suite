"""Check plugins.

Importing this package imports every check module, which triggers their
`@register` decorators and populates the registry. Add a new check by dropping a
module here and importing it below.
"""

from . import http_headers  # noqa: F401  (import for side-effect: registration)
from . import file_permissions  # noqa: F401
from . import tls_cert  # noqa: F401
