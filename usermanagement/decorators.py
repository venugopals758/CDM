from functools import wraps

from django.contrib.auth.decorators import user_passes_test
from django.http import JsonResponse, HttpResponse
from django.shortcuts import redirect
from usermanagement.models import *
from usermanagement.encryption_util import *
from django.contrib import messages

def group_required(*group_names):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            user = request.user
            if user.is_authenticated and user.is_active:
                if UserGroups.objects.filter(
                    user_id=user.id,
                    group__name__in=group_names,
                    is_active=1
                ).exists():
                    return view_func(request, *args, **kwargs)
            messages.error(request,'Permission Denied')
            return redirect('/dashboard')
        return _wrapped_view
    return decorator
