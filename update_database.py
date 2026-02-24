from tools.db_auth import register_user

register_user('admin', 'admin', quota_gb=10, is_admin=True)
