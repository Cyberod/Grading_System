from functools import wraps
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib import messages

def user_type_required(user_types):
    """
    Decorator to restrict access based on user type.
    Usage: @user_type_required(['student']) or @user_type_required(['teacher', 'admin'])
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            
            if request.user.user_type not in user_types:
                messages.error(request, 'You do not have permission to access this page.')
                return redirect('dashboard')
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

def student_required(view_func):
    """Decorator to restrict access to students only."""
    return user_type_required(['student'])(view_func)

def teacher_required(view_func):
    """Decorator to restrict access to teachers only."""
    return user_type_required(['teacher'])(view_func)
