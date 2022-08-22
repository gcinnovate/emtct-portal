from functools import wraps

from django.urls import reverse


def two_factor_auth(f):
    @wraps(f)
    def g(request, *args, **kwargs):
        if request.user.is_authenticated and "verified_user" in request.session:
            return f(request, *args, **kwargs)
        else:
            if (request.user.is_authenticated()):
                return reverse('submit-code')
            else:
                return reverse('login')
    return g


## Ref: https://stackoverflow.com/questions/51308060/possible-to-use-mixins-in-function-based-views