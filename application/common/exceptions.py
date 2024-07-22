class UnravelBackendError(Exception):
    def __init__(self, *args, **kwargs):
        if len(args) == 0:
            args = ['Something went wrong']
        super().__init__(*args, **kwargs)
        self.http_response_code = 500  # Internal Server Error


class AuthenticationException(Exception):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.http_response_code = 401  # unauthorized


class AuthorizationException(Exception):

    def __init__(self, *args, **kwargs):
        if len(args) == 0:
            args = ['You are not authorised to perform this action.']
        super().__init__(*args, **kwargs)
        self.http_response_code = 403  # forbidden

