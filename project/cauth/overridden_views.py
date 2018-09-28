import django.contrib.auth.views

import cauth.forms


def password_change(request):
    template_response = django.contrib.auth.views.password_change(
        request,
        password_change_form=cauth.forms.PasswordChangeForm,
        extra_context={'disable_change_password_warning': True}
    )
    # Do something with `template_response`
    return template_response
