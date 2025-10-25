from django.shortcuts import redirect
from django.conf import settings
from django.urls import reverse

EXEMPT_URLS = [reverse("login")]  # add more if needed

class LoginRequiredMiddleware:
    """
    Middleware that requires a user to be authenticated to access any page
    except specified exempt URLs.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.user.is_authenticated:
            path = request.path_info

            # skip admin and exempt urls
            if not (path.startswith("/admin/") or path in EXEMPT_URLS):
                return redirect(settings.LOGIN_URL)  # use your login view name

        return self.get_response(request)
