class OEmbedException(Exception):
    pass

class OEmbedInvalidResource(OEmbedException):
    pass

class OEmbedMissingEndpoint(OEmbedException):
    pass

class OEmbedBadRequest(OEmbedException):
    pass

class OEmbedHTTPException(OEmbedException):
    pass

class AlreadyRegistered(OEmbedException):
    """Raised when a model is already registered with a site."""
    pass

class NotRegistered(OEmbedException):
    """Raised when a model is not registered with a site."""
    pass
