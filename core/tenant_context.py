"""
Contextvar che tiene traccia del tenant corrente durante una request
(o durante uno script di management/console). E' la base dell'isolamento
multi-tenant a schema condiviso: ogni query passante da TenantManager
viene filtrata su questo valore.
"""
from contextvars import ContextVar

_current_tenant_id: ContextVar = ContextVar("current_tenant_id", default=None)


def set_current_tenant(tenant_id):
    _current_tenant_id.set(tenant_id)


def get_current_tenant_id():
    return _current_tenant_id.get()


def clear_current_tenant():
    _current_tenant_id.set(None)
