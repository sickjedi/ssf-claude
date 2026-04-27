import logging

_logger = logging.getLogger('ssf.audit')


def log_action(action: str, resource: str, detail: str) -> None:
    from flask_login import current_user
    try:
        user = current_user.email if current_user.is_authenticated else 'anonymous'
    except Exception:
        user = 'unknown'
    _logger.info('%s | %s | %s | %s', user, action, resource, detail)
