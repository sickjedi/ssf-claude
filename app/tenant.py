from flask import g, session, abort
from flask_login import current_user


def _resolve_tenant():
    if not current_user.is_authenticated:
        return None
    from app.models.user import Role
    if current_user.role == Role.SUPER_ADMIN:
        tenant_id = session.get('tenant_id')
        if tenant_id:
            from app import db
            from app.models.organisation import Organisation
            return db.session.get(Organisation, tenant_id)
        return None
    return current_user.member.organisation if current_user.member else None


def init_tenant(app):
    @app.before_request
    def set_tenant():
        g.tenant = _resolve_tenant()


def require_tenant():
    if g.get('tenant') is None:
        abort(403)
