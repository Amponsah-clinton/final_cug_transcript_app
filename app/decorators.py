from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps

def superadmin_required(view_func):
    """
    Only allows users who are staff or superusers to access the view.
    Redirects others to the dashboard with an error message.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "You must be logged in to access this page.")
            return redirect('login')  # change to your login URL name

        if not request.user.is_superuser:
            messages.error(request, "You don’t have permission to access this page.")
            return redirect('dashboard')  # change to your dashboard URL name

        return view_func(request, *args, **kwargs)
    return wrapper
