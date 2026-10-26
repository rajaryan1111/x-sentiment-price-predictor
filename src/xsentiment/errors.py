"""Typed errors used across ingestion and storage boundaries."""

class PipelineError(Exception):
    """Base class for expected pipeline failures."""


class NetworkError(PipelineError):
    """A source request failed at the transport layer."""


class RateLimitError(NetworkError):
    """A remote provider asked the client to slow down."""


class BlockedSourceError(NetworkError):
    """A provider rejected access to a source."""


class PayloadTooLargeError(NetworkError):
    """A response exceeded the configured size ceiling."""


class TimeoutErrorPipeline(NetworkError):
    """A source request timed out."""
