def access_context(request):
    return {
        'access_code_verified': False,  # код не запоминается в сессии (п.1)
        'has_access_code': bool(
            request.user.is_authenticated and
            hasattr(request.user, 'access_code_hash') and
            request.user.access_code_hash
        ),
        'current_child_id': request.session.get('current_child_id'),
    }
