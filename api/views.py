from datetime import datetime
from threading import Thread

from django.contrib.auth.models import User
from django.core.handlers.base import logger
from django.db.models import Q
from django.http import HttpResponse
from rest_framework import viewsets, status
from rest_framework.decorators import action, permission_classes
from rest_framework.parsers import FileUploadParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from api.permissions import IsTrainer, IsCoach, IsRoot
from event_api.models import SaveFile, Wildcard, StreamerWildcardInventoryItem, WildcardLog, Streamer
from event_api.serializers import SaveFileSerializer, WildcardSerializer, WildcardWithInventorySerializer, \
    SimplifiedWildcardSerializer
from pokemon_api.models import Move
from pokemon_api.scripting.save_reader import get_trainer_name, data_reader
from pokemon_api.serializers import MoveSerializer
from rewards_api.serializers import StreamerRewardSerializer
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
    def get_rewards(self, request, *args, **kwargs):
        trainer: Trainer = Trainer.get_from_user(request.user)
        logger.debug(str(trainer))
        streamer = trainer.get_streamer()

        serializer = StreamerRewardSerializer(streamer.rewards.all(), many=True)

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
        serializer = SelectTrainerSerializer(Trainer.objects.all().order_by('streamer__name'), many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=['get'], detail=False)
    def wildcards_with_inventory(self, request, *args, **kwargs):
        trainer = Trainer.get_from_user(request.user)

        serializer = WildcardWithInventorySerializer(
            Wildcard.objects.filter(is_active=True),
            trainer=trainer,
            many=True
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=['get'], detail=True)
    def list_boxes(self, request, pk=None, *args, **kwargs):
        if pk == 'undefined':
            return Response(status=status.HTTP_400_BAD_REQUEST)
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

    @action(methods=['get'], detail=True)
    @permission_classes([IsRoot])
    def reload_team_by_trainer(self, request, *args, **kwargs):
        trainer = self.get_object()
        last_save: SaveFile = trainer.saves.all().order_by('created_on').last()
        file_obj = last_save.file.file
        save_data = file_obj.read()
        save_results = data_reader(save_data)
        team_saver(save_results.get('team'), trainer)

        return Response(data=dict(detail=f'Reloaded {trainer.name}\'s team'), status=status.HTTP_200_OK)

    @action(methods=['get'], detail=False)
    @permission_classes([IsRoot])
    def reload_boxes(self, request, *args, **kwargs):
        trainers = self.get_queryset()
        total_trainers = trainers.count()
        for index, trainer in enumerate(trainers):
            print(f'{index + 1}/{total_trainers} - {trainer.name} @ {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
            last_save: SaveFile = trainer.saves.all().order_by('created_on').last()
            file_obj = last_save.file.file
            save_data = file_obj.read()
            save_results = data_reader(save_data)
            box_saver(save_results.get('boxes'), trainer)

        return Response(data=dict(detail=f'Reloaded {total_trainers} trainer\'s boxes'), status=status.HTTP_200_OK)

    @action(methods=['get'], detail=True)
    @permission_classes([IsRoot])
    def reload_by_trainer_boxes(self, request, *args, **kwargs):
        trainer = self.get_object()
        last_save: SaveFile = trainer.saves.all().order_by('created_on').last()
        file_obj = last_save.file.file
        save_data = file_obj.read()
        save_results = data_reader(save_data)
        box_saver(save_results.get('boxes'), trainer)

        return Response(data=dict(
            detail=f'Reloaded {trainer.name} boxes'
        ), status=status.HTTP_200_OK)

    @action(methods=['get'], detail=True)
    def box(self, request, pk=None, *args, **kwargs):
        if pk == 'undefined':
            return Response(status=status.HTTP_400_BAD_REQUEST)
        trainer = Trainer.objects.get(id=pk)
        box_id = request.query_params.get('box', 0)
        box = trainer.boxes.filter(box_number=box_id).last()
        box_serializer = TrainerBoxSerializer(box, read_only=True)

        return Response(box_serializer.data, status=status.HTTP_200_OK)

    @action(methods=['get'], detail=False)
    def last_save(self, request, *args, **kwargs):
        trainer: Trainer = Trainer.get_from_user(request.user)
        last_save = trainer.saves.order_by('created_on').last()
        print(trainer)
        return HttpResponse(last_save.file.read())

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


class WildcardViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Wildcard.objects.filter(is_active=True)
    serializer_class = WildcardSerializer

    @action(methods=['GET'], detail=False)
    def simplified(self, request, *args, **kwargs):
        serializer = SimplifiedWildcardSerializer(self.get_queryset(), many=True)
        return Response(serializer.data)

    @action(methods=['POST'], detail=True)
    def use_card(self, request, *args, **kwargs):
        wildcard: Wildcard = self.get_object()
        quantity = int(request.data.get('quantity', 1))
        trainer = Trainer.get_from_user(request.user)
        if wildcard.can_use(trainer, quantity):
            if wildcard.use(trainer, quantity):
                return Response(data=dict(detail='card_used'), status=status.HTTP_200_OK)
            return Response(data=dict(detail='contact_paramada'), status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(data=dict(detail='no_card_available'), status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['POST'], detail=True)
    def buy_card(self, request, *args, **kwargs):
        wildcard: Wildcard = self.get_object()
        quantity = int(request.data.get('quantity', 1))
        trainer = Trainer.get_from_user(request.user)
        if wildcard.can_buy(trainer, quantity, True):
            if wildcard.buy(trainer, quantity, True):
                return Response(data=dict(detail='card_bought'), status=status.HTTP_200_OK)
            return Response(data=dict(detail='contact_paramada'), status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(data=dict(detail='no_enough_money'), status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['POST'], detail=True)
    def buy_and_use_card(self, request, *args, **kwargs):
        wildcard: Wildcard = self.get_object()
        quantity = int(request.data.get('quantity', 1))
        trainer = Trainer.get_from_user(request.user)
        if wildcard.can_buy(trainer, quantity):
            buyed = wildcard.buy(trainer, quantity)
            used = wildcard.use(trainer, quantity)
            if buyed and used:
                return Response(data=dict(detail='card_bought_and_used', amount=buyed), status=status.HTTP_200_OK)
            return Response(data=dict(detail='contact_paramada'), status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(data=dict(detail='no_enough_money'), status=status.HTTP_400_BAD_REQUEST)


def team_saver(team, trainer):
    new_version = TrainerTeam.objects.filter(trainer_old=trainer).count() + 1
    team_data = dict(
        version=new_version,
        trainer_old=trainer.pk,
        team=[pokemon for pokemon in team if pokemon]
    )

    for pokemon in team:
        if not trainer.current_team:
            continue
        if not pokemon:
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


def box_saver(boxes, trainer: Trainer):
    trainer.boxes.all().delete()

    for box_num in range(31):
        TrainerBox.objects.get_or_create(box_number=box_num, trainer=trainer)

    for box_num, data in boxes.items():
        if not data:
            continue
        box = TrainerBox.objects.get(box_number=box_num, trainer=trainer)
        for slot in data:
            box_slot, _ = TrainerBoxSlot.objects.get_or_create(box=box, slot=slot['slot'])
            pokemon = slot['pokemon']
            pokemon_serializer = TrainerPokemonSerializer(data=pokemon)
            if pokemon_serializer.is_valid(raise_exception=True):
                pokemon = pokemon_serializer.save()
                box_slot.pokemon = pokemon
                box_slot.save()

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
        total_trainers = len(files)
        for index, file_obj in enumerate(files):
            save_data = file_obj.file.read()
            file_obj.seek(0)
            trainer_name = get_trainer_name(save_data)
            trainer, is_created = Trainer.objects.get_or_create(name=trainer_name)
            print(f'{index + 1}/{total_trainers} - {trainer_name} @ {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')

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

