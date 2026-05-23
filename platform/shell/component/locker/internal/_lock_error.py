class LockError(RuntimeError):
    """Raised when the node is already locked by another live process."""
