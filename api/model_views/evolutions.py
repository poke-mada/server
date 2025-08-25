import json
from rest_framework import status
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from event_api.models import Evolution


class EvolutionsUploadView(APIView):
    permission_classes = []
    parser_class = (MultiPartParser,)

    def post(self, request, *args, **kwargs):
        file_obj = request.data['file'].file
        json_data = json.load(file_obj)
        Evolution.objects.all().delete()
        for dex_number, root_dex_number in json_data.items():
            Evolution.objects.create(
                dex_number=dex_number,
                root_evolution=root_dex_number
            )

        return Response(data=dict(status='done'), status=status.HTTP_201_CREATED)
