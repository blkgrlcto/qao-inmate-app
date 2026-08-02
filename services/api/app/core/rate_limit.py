"""Rate limiting configuration.

In-memory limiter — fine for a single-process deployment. If the API ever
runs as multiple replicas, this needs a shared backend (e.g. Redis) or each
replica enforces its own independent limit.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
