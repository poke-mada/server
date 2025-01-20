from threading import Thread

from django.contrib.auth.models import User
from django.db.models import Q
from django.http import HttpResponse
from rest_framework import viewsets, status
from rest_framework.decorators import action, permission_classes
from rest_framework.parsers import FileUploadParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from api.permissions import IsTrainer, IsCoach, IsRoot
from event_api.models import SaveFile
from event_api.serializers import SaveFileSerializer
from pokemon_api.models import Move
from pokemon_api.scripting.save_reader import get_trainer_name, data_reader
from pokemon_api.serializers import MoveSerializer
from trainer_data.models import Trainer, TrainerTeam, TrainerBox, TrainerBoxSlot
from trainer_data.serializers import TrainerSerializer, TrainerTeamSerializer, SelectTrainerSerializer, \
    TrainerBoxSerializer, TrainerPokemonSerializer, EnTrainerSerializer, ListedBoxSerializer


# Create your views here.

class TrainerViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Trainer.objects.filter(is_active=True)
    serializer_class = TrainerSerializer

    def _get_queryset(self):
        user: User = self.request.user
        filters = Q()
        if not user.is_superuser:
            if user.coaching_profile:
                filters |= Q(pk=user.coaching_profile.coached_trainer.pk)
            if user.trainer_profile:
                filters |= Q(pk=user.trainer_profile.trainer.pk)
        return self.queryset.filter(filters)

    @action(methods=['get'], detail=False)
    @permission_classes([IsTrainer])
    def get_trainer(self, request, *args, **kwargs):
        user: User = request.user
        if hasattr(user, 'trainer_profile') and user.trainer_profile.trainer:
            trainer = user.trainer_profile.trainer
        elif hasattr(user, 'coaching_profile') and user.coaching_profile.coached_trainer:
            trainer = user.coaching_profile.coached_trainer
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(trainer)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=['get'], detail=False)
    @permission_classes([IsCoach])
    def get_coached_trainer(self, request, *args, **kwargs):
        user: User = request.user
        trainer = user.coaching_profile.coached_trainer
        serializer = self.get_serializer(trainer)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=['get'], detail=False)
    @permission_classes([IsTrainer])
    def get_economy(self, request, *args, **kwargs):
        user: User = request.user
        if user.trainer_profile and user.trainer_profile.trainer:
            trainer = user.trainer_profile.trainer
        elif user.coaching_profile and user.coaching_profile.coached_trainer:
            trainer = user.coaching_profile.coached_trainer
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        return Response(trainer.economy, status=status.HTTP_200_OK)

    @action(methods=['get'], detail=False)
    def list_trainers(self, request, *args, **kwargs):
        serializer = SelectTrainerSerializer(Trainer.objects.all(), many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=['get'], detail=True)
    def list_boxes(self, request, pk=None, *args, **kwargs):
        trainer = Trainer.objects.get(id=pk)
        serializer = ListedBoxSerializer(trainer.boxes.all(), many=True, read_only=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=['get'], detail=False)
    @permission_classes([IsRoot])
    def reload_teams(self, request, *args, **kwargs):
        trainers = self.queryset
        for trainer in trainers:
            last_save: SaveFile = trainer.saves.all().order_by('created_on').last()
            file_obj = last_save.file.file
            save_data = file_obj.read()
            save_results = data_reader(save_data)
            team_saver(save_results.get('team'), trainer)

        return Response([], status=status.HTTP_200_OK)

    @action(methods=['get'], detail=False)
    @permission_classes([IsRoot])
    def reload_boxes(self, request, *args, **kwargs):
        trainers = self.get_queryset()
        for trainer in trainers:
            last_save: SaveFile = trainer.saves.all().order_by('created_on').last()
            file_obj = last_save.file.file
            save_data = file_obj.read()
            save_results = data_reader(save_data)
            box_saver(save_results.get('boxes'), trainer)

        return Response([], status=status.HTTP_200_OK)

    @action(methods=['get'], detail=True)
    def box(self, request, pk=None, *args, **kwargs):
        trainer = Trainer.objects.get(id=pk)
        box_id = request.query_params.get('box', 0)
        box = trainer.boxes.filter(box_number=box_id).last()
        box_serializer = TrainerBoxSerializer(box, read_only=True)

        return Response(box_serializer.data, status=status.HTTP_200_OK)

    def retrieve(self, request, pk=None, *args, **kwargs):
        localization = request.query_params.get('localization', '*')
        trainer = Trainer.objects.get(id=pk)
        match localization:
            case 'en':
                serialized = EnTrainerSerializer(trainer)
            case _:
                serialized = TrainerSerializer(trainer)

        return Response(serialized.data, status=status.HTTP_200_OK)


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
        box.slots.all().delete()
        for slot in data:
            box_slot, _ = TrainerBoxSlot.objects.get_or_create(box=box, slot=slot['slot'])
            pokemon_serializer = TrainerPokemonSerializer(data=slot['pokemon'])
            if pokemon_serializer.is_valid(raise_exception=True):
                pokemon = pokemon_serializer.save()
                box_slot.pokemon = pokemon

    return False


class FileUploadView(APIView):
    permission_classes = [IsAuthenticated, ]
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


class TrainerSaveView(APIView):
    permission_classes = [IsAuthenticated, ]

    def get(self, request, trainer_name, *args, **kwargs):
        trainer = Trainer.objects.get(name=trainer_name)
        last_save = trainer.saves.order_by('created_on').last()
        return HttpResponse(last_save.file.read())
