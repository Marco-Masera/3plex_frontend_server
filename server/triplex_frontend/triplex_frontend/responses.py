from rest_framework.response import Response
from rest_framework import status
from django.http import JsonResponse
from django.forms import model_to_dict
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Model
import json


class ExtendedEncoder(DjangoJSONEncoder):
    def default(self, o):
        if isinstance(o, Model):
            return model_to_dict(o)
        return super().default(o)

class Responses:
    def success(payload):
        data = json.dumps({ 'success': True, 'payload': payload }, cls=ExtendedEncoder)
        return Response(data)

    def success_json(data):
        return JsonResponse(data, safe=False)

    def generic_failure(message: str = "Internal server error", errorCode: status = status.HTTP_500_INTERNAL_SERVER_ERROR):
        data = json.dumps({ 'success': False, 'error': message }, cls=ExtendedEncoder)
        return Response(data, status=errorCode)
    
