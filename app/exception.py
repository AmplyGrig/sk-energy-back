from sanic_jwt import exceptions

class RegistrationFailed(exceptions.SanicJWTException):
    status_code = 402

    def __init__(self, message="Registration failed.", **kwargs):
        super().__init__(message, **kwargs)

class PasswordResetFailed(exceptions.SanicJWTException):
    status_code = 403

    def __init__(self, message="Password reset failed.", **kwargs):
        super().__init__(message, **kwargs)

class UserException(exceptions.SanicJWTException):
    status_code = 405

    def __init__(self, message="User error.", **kwargs):
        super().__init__(message, **kwargs)

class ObjectException(exceptions.SanicJWTException):
    status_code = 406

    def __init__(self, message="Object error.", **kwargs):
        super().__init__(message, **kwargs)