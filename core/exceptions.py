from django.core.exceptions import PermissionDenied
from django.http import Http404
from rest_framework import status
from rest_framework.exceptions import APIException, NotAuthenticated
from rest_framework.response import Response
from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    
    if response is None:
        if isinstance(exc, Http404):
            response = Response(
                {"detail": "Not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        elif isinstance(exc, PermissionDenied):
            response = Response(
                {"detail": "Permission denied."},
                status=status.HTTP_403_FORBIDDEN
            )
        elif isinstance(exc, NotAuthenticated):
            response = Response(
                {"detail": "Authentication credentials were not provided."},
                status=status.HTTP_401_UNAUTHORIZED
            )
        else:
            response = Response(
                {"detail": "A server error occurred."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    if response is not None:
        response_data = response.data
        
        if isinstance(response_data, str):
            response.data = {"detail": response_data}
        
        response.data["status_code"] = response.status_code
    
    return response


class ResourceConflictError(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "A resource conflict has occurred."
    default_code = "resource_conflict"


class InvalidOperationError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "This operation cannot be performed in the current state."
    default_code = "invalid_operation"