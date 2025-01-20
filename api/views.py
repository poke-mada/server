from django.http import FileResponse, HttpResponse
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.parsers import FileUploadParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from event_api.models import SaveFile
from event_api.serializers import SaveFileSerializer
from pokemon_api.models import Move
from pokemon_api.scripting.save_reader import get_trainer_name, data_reader
from pokemon_api.serializers import MoveSerializer
from trainer_data.models import Trainer, TrainerTeam, TrainerBox, TrainerBoxSlot
from trainer_data.serializers import TrainerSerializer, TrainerTeamSerializer, SelectTrainerSerializer, \
    TrainerBoxSerializer, TrainerPokemonSerializer, EnTrainerSerializer


# Create your views here.

class TrainerViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Trainer.objects.all()
    serializer_class = TrainerSerializer

    @action(methods=['get'], detail=False)
    def list_trainers(self, request, *args, **kwargs):
        serializer = SelectTrainerSerializer(Trainer.objects.all(), many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=['get'], detail=False)
    def reload_teams(self, request, *args, **kwargs):
        trainers = self.get_queryset()
        for trainer in trainers:
            last_save: SaveFile = trainer.saves.all().order_by('created_on').last()
            file_obj = last_save.file.file
            save_data = file_obj.read()
            save_results = data_reader(save_data)
            team_saver(save_results.get('team'), trainer)

        return Response([], status=status.HTTP_200_OK)

    @action(methods=['get'], detail=False)
    def reload_boxes(self, request, *args, **kwargs):
        trainers = self.get_queryset()
        for trainer in trainers:
            last_save: SaveFile = trainer.saves.all().order_by('created_on').last()
            file_obj = last_save.file.file
            save_data = file_obj.read()
            save_results = data_reader(save_data)
            box_saver(save_results.get('boxes'), trainer)

        return Response([], status=status.HTTP_200_OK)


class MoveViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Move.objects.all()
    serializer_class = MoveSerializer


def team_saver(team, trainer):
    new_version = TrainerTeam.objects.filter(trainer_old=trainer).count() + 1
    team_data = dict(
        version=new_version,
        trainer_old=trainer.pk,
        team=team
    )

    for pokemon in team:
        if not trainer.current_team:
            continue
        last_version = trainer.current_team.team.filter(mote=pokemon['mote']).first()
        if last_version:
            pokemon['notes'] = last_version.notes

    new_team_serializer = TrainerTeamSerializer(data=team_data)
    if new_team_serializer.is_valid(raise_exception=True):
        new_team_obj = new_team_serializer.save()
        trainer.current_team = new_team_obj
        trainer.save()
        return True
    return False


def box_saver(boxes, trainer):
    for box_num in range(31):
        TrainerBox.objects.get_or_create(box_number=box_num, trainer=trainer)

    for box_num, data in boxes.items():
        box = TrainerBox.objects.get(box_number=box_num, trainer=trainer)
        for slot in data:
            pokemon_serializer = TrainerPokemonSerializer(data=slot['pokemon'])
            if pokemon_serializer.is_valid(raise_exception=True):
                pokemon = pokemon_serializer.save()
                TrainerBoxSlot.objects.get_or_create(box=box, slot=slot['slot'], pokemon=pokemon)

    return False


class FileUploadView(APIView):
    permission_classes = [IsAuthenticated,]
    parser_class = (FileUploadParser,)

    def post(self, request, *args, **kwargs):
        file_obj = request.data['file'].file
        save_data = file_obj.read()
        file_obj.seek(0)
        trainer_name = get_trainer_name(save_data)
        trainer, is_created = Trainer.objects.get_or_create(name=trainer_name)

        data = dict(
            file=request.data['file'],
            trainer=trainer.pk
        )
        file_serializer = SaveFileSerializer(data=data)

        if file_serializer.is_valid():
            file_serializer.save()
            save_results = data_reader(save_data)
            team_saver(save_results.get('team'), trainer)
            box_saver(save_results.get('boxes'), trainer)
        else:
            return Response(file_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response(file_serializer.data, status=status.HTTP_201_CREATED)


class FileUploadManyView(APIView):
    permission_classes = []
    parser_class = (MultiPartParser,)

    def post(self, request, *args, **kwargs):
        files = request.FILES.getlist('files')
        for file_obj in files:
            save_data = file_obj.file.read()
            file_obj.seek(0)
            trainer_name = get_trainer_name(save_data)
            trainer, is_created = Trainer.objects.get_or_create(name=trainer_name)

            data = dict(
                file=file_obj,
                trainer=trainer.pk
            )
            file_serializer = SaveFileSerializer(data=data)

            if file_serializer.is_valid():
                file_serializer.save()
                save_results = data_reader(save_data)
                team_saver(save_results.get('team'), trainer)
                box_saver(save_results.get('boxes'), trainer)
            else:
                return Response(file_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response(data=dict(status='done'), status=status.HTTP_201_CREATED)


class TrainerView(APIView):
    permission_classes = [IsAuthenticated,]

    def get(self, request, trainer_name, *args, **kwargs):
        localization = request.query_params.get('localization', '*')
        trainer = Trainer.objects.get(name=trainer_name)
        match localization:
            case 'en':
                serialized = EnTrainerSerializer(trainer)
            case _:
                serialized = TrainerSerializer(trainer)
        return Response(data=serialized.data, status=status.HTTP_200_OK)


class TrainerEconomyView(APIView):
    permission_classes = []

    def get(self, request, trainer_name, *args, **kwargs):
        trainer = Trainer.objects.get(name=trainer_name)
        return Response(data=trainer.economy, status=status.HTTP_200_OK)


class TrainerSaveView(APIView):
    permission_classes = [IsAuthenticated,]

    def get(self, request, trainer_name, *args, **kwargs):
        trainer = Trainer.objects.get(name=trainer_name)
        last_save = trainer.saves.order_by('created_on').last()
        return HttpResponse(last_save.file.read())


class TrainerBoxView(APIView):
    permission_classes = []

    def get(self, request, trainer_name, *args, **kwargs):
        trainer = Trainer.objects.get(name=trainer_name)
        box_serializer = TrainerBoxSerializer(trainer.boxes.all(), many=True, read_only=True)

        return Response(data=box_serializer.data, status=status.HTTP_200_OK)
