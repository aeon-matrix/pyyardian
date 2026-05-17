class NotAuthorizedException(Exception):
    """Exception raised when the client is not authorized."""

class NetworkException(Exception):
    """Exception raised when cannot connect to device."""