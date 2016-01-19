def get_request_ip(request):
    # TODO: also handle requests passed through proxy
    # x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    # x_forwarded_for.split(',')[-1].strip()

    # if running behind nginx/IIS reverse proxy
    ip = request.META.get('HTTP_X_REAL_IP')
    if ip is not None:
        return ip

    ip = request.META.get('REMOTE_ADDR')
    return ip
