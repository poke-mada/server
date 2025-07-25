from datetime import datetime

import requests
from django.contrib.auth.models import User
from django.core.handlers.base import logger
from django.db.models import Q
from django.http import HttpResponse, FileResponse
from rest_framework import viewsets, status
from rest_framework.decorators import action, permission_classes
from rest_framework.parsers import FileUploadParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from api.permissions import IsTrainer, IsRoot
from event_api.models import SaveFile, Wildcard, Streamer, CoinTransaction, \
    GameEvent, DeathLog, MastersProfile, ProfileImposterLog, Imposter, Newsletter, MastersSegment, \
    MastersSegmentSettings
from event_api.serializers import SaveFileSerializer, WildcardSerializer, WildcardWithInventorySerializer, \
    SimplifiedWildcardSerializer, GameEventSerializer, SelectProfileSerializer, ProfileSerializer
from pokemon_api.models import Move, Pokemon, Item, ItemNameLocalization
from pokemon_api.scripting.save_reader import get_trainer_name, data_reader
from pokemon_api.serializers import MoveSerializer, ItemSelectSerializer
from rewards_api.models import RewardBundle, StreamerRewardInventory
from rewards_api.serializers import StreamerRewardSerializer, StreamerRewardSimpleSerializer
from trainer_data.models import Trainer, TrainerTeam, TrainerBox, TrainerBoxSlot
from trainer_data.serializers import TrainerSerializer, TrainerTeamSerializer, SelectTrainerSerializer, \
    TrainerBoxSerializer, TrainerPokemonSerializer, EnTrainerSerializer, ListedBoxSerializer, \
    EnROTrainerPokemonSerializer, ROTrainerPokemonSerializer, NewsletterSerializer


# Create your views here.

class TrainerViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Trainer.objects.filter(is_active=True)
    serializer_class = TrainerSerializer
    permission_classes = [IsTrainer]

    def _get_queryset(self):
        user: User = self.request.user
        filters = Q()
        if not user.is_superuser:
            if user.masters_profile.profile_type != MastersProfile.ADMIN:
                filters |= Q(pk=user.masters_profile.trainer.pk)
        return self.queryset.filter(filters)

    @action(methods=['get'], detail=False)
    def get_trainer(self, request, *args, **kwargs):
        user: User = request.user
        trainer = Trainer.get_from_user(user)
        if not trainer:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(trainer)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=['get'], detail=False, permission_classes=[])
    def get_deaths(self, request, *args, **kwargs):
        streamer_name = request.GET.get('streamer', False)
        streamer = Streamer.objects.filter(name=streamer_name).first()
        profile = streamer.user.masters_profile
        return Response(data=dict(death_count=profile.death_count), status=status.HTTP_200_OK)

    @action(methods=['get'], detail=False, permission_classes=[])
    def get_data(self, request, *args, **kwargs):
        from websocket.serializers import OverlaySerializer
        streamer_name = request.GET.get('streamer', False)
        streamer = Streamer.objects.filter(name=streamer_name).first()
        if not streamer:
            return Response(status=status.HTTP_404_NOT_FOUND)

        profile = streamer.user.masters_profile
        serializer = OverlaySerializer(profile.trainer)

        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @action(methods=['post'], detail=False)
    def register_death(self, request, *args, **kwargs):
        from websocket.sockets import OverlayConsumer
        user: User = request.user
        profile = user.masters_profile
        trainer = Trainer.get_from_user(user)
        pid = request.data.get('pid')
        mote = request.data.get('mote')
        dex_number = request.data.get('species')
        species = Pokemon.objects.filter(dex_number=dex_number).first().name
        _, is_created = DeathLog.objects.get_or_create(profile=profile, trainer=trainer, pid=pid, mote=mote, species_name=species)

        if is_created:
            current_segment: MastersSegmentSettings = profile.current_segment_settings
            current_segment.death_count += 1
            current_segment.save()

            profile.death_count += 1
            profile.save()

        OverlayConsumer.send_overlay_data(profile.streamer_name)
        serializer = self.get_serializer(trainer)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=['get'], detail=False)
    def get_rewards(self, request, *args, **kwargs):
        profile = request.user.masters_profile
        bundles = RewardBundle.objects.filter(owners__profile=profile, owners__is_available=True)
        serializer = StreamerRewardSimpleSerializer(bundles, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=['post'],
            detail=False,
            url_path='claim_reward/(?P<reward_id>[0-9a-fA-F-]{36})',
            permission_classes=[IsTrainer])
    def claim_reward(self, request, *args, **kwargs):
        user: User = request.user
        reward_id = kwargs.pop('reward_id')
        if not reward_id:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        trainer: Trainer = Trainer.get_from_user(request.user)
        logger.debug(str(trainer))
        profile: MastersProfile = user.masters_profile
        reward_inventory: StreamerRewardInventory = profile.reward_inventory.filter(reward_id=reward_id, is_available=True).first()
        if not reward_inventory:
            return Response(status=status.HTTP_404_NOT_FOUND)

        bundle = reward_inventory.reward

        for reward in bundle.rewards.all():
            if not reward.is_active:
                continue

            if reward.reward_type == reward.MONEY:
                CoinTransaction.objects.create(
                    profile=user.masters_profile,
                    amount=reward.quantity,
                    TYPE=CoinTransaction.INPUT,
                    reason=f'Se obtuvo {reward.quantity} moneda/s al canjear el premio {bundle.id}'
                )
            elif reward.reward_type == reward.WILDCARD:
                inventory, _ = profile.wildcard_inventory.get_or_create(
                    wildcard=reward.wildcard,
                    defaults=dict(quantity=0)
                )
                inventory.quantity += reward.quantity
                inventory.save()

        reward_inventory.exchanges += 1
        if not user.is_superuser:
            reward_inventory.is_available = False
        reward_inventory.save()

        serializer = StreamerRewardSerializer(reward_inventory.reward)

        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=['get'], detail=False)
    def get_economy(self, request, *args, **kwargs):
        user: User = request.user
        current_profile: MastersProfile = user.masters_profile

        if not current_profile:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        if current_profile.profile_type == MastersProfile.COACH:
            return Response(current_profile.coached.economy, status=status.HTTP_200_OK)

        return Response(user.masters_profile.economy, status=status.HTTP_200_OK)

    @action(methods=['post'], detail=False)
    def register_imposter(self, request, *args, **kwargs):
        message = request.data.get('message')
        user: User = request.user
        current_profile: MastersProfile = user.masters_profile

        if not current_profile:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        if current_profile.profile_type == MastersProfile.COACH:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        imposter = Imposter.objects.filter(message__iexact=message).first()

        ProfileImposterLog.objects.get_or_create(
            profile=current_profile,
            imposter=imposter
        )

        trainer = Trainer.get_from_user(user)
        serializer = self.get_serializer(trainer)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=['get'], detail=False)
    def get_wildcard_count(self, request, *args, **kwargs):
        user: User = request.user
        current_profile: MastersProfile = user.masters_profile

        if not current_profile:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        if current_profile.profile_type == MastersProfile.COACH:
            return Response(current_profile.coached.wildcard_count, status=status.HTTP_200_OK)

        return Response(user.masters_profile.wildcard_count, status=status.HTTP_200_OK)

    @action(methods=['get'], detail=False)
    def list_trainers(self, request, *args, **kwargs):
        user: User = request.user
        is_tester = user.masters_profile.is_tester
        is_pro = user.masters_profile.is_pro
        trainer_ids = MastersProfile.objects.filter(is_pro=is_pro, profile_type=MastersProfile.TRAINER,
                                                    is_tester=is_tester,
                                                    trainer__isnull=False).values_list('trainer', flat=True)
        trainers = Trainer.objects.filter(id__in=trainer_ids)
        serializer = SelectTrainerSerializer(trainers, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=['get'], detail=False)
    def wildcards_with_inventory(self, request, *args, **kwargs):
        current_profile: MastersProfile = request.user.masters_profile
        trainer_user = request.user
        if current_profile.profile_type == MastersProfile.COACH:
            trainer_user = current_profile.coached.user

        serializer = WildcardWithInventorySerializer(
            Wildcard.objects.filter(is_active=True),
            user=trainer_user,
            many=True
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=['get'], detail=True)
    def list_boxes(self, request, pk=None, *args, **kwargs):
        clean_pk = pk
        if pk == 'undefined' or pk == 0 or pk == '0':
            current_profile: MastersProfile = request.user.masters_profile
            clean_pk = current_profile.trainer_id

        trainer = Trainer.objects.filter(id=clean_pk).first()
        if trainer is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = ListedBoxSerializer(trainer.boxes.all().order_by('box_number'), many=True, read_only=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=['get'], detail=False)
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
    def reload_team_by_trainer(self, request, *args, **kwargs):
        trainer = self.get_object()
        last_save: SaveFile = trainer.saves.all().order_by('created_on').last()
        file_obj = last_save.file.file
        save_data = file_obj.read()
        save_results = data_reader(save_data)
        team_saver(save_results.get('team'), trainer)

        return Response(data=dict(detail=f'Reloaded {trainer.name}\'s team'), status=status.HTTP_200_OK)

    @action(methods=['get'], detail=False)
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
        if pk == 'undefined' or pk == 0 or pk == '0':
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

    @action(methods=['get'], detail=False)
    def get_team(self, request, *args, **kwargs):
        user: User = request.user
        localization = request.query_params.get('localization', '*')
        trainer = Trainer.get_from_user(user)
        match localization:
            case 'en':
                serialized = EnROTrainerPokemonSerializer(trainer.current_team.team, many=True)
            case _:
                serialized = ROTrainerPokemonSerializer(trainer.current_team.team, many=True)

        return Response(serialized.data, status=status.HTTP_200_OK)

    @action(methods=['get'], detail=False)
    def list_players(self, request, *args, **kwargs):
        user: User = request.user
        current_profile = user.masters_profile
        profiles = MastersProfile.objects.filter(is_pro=current_profile.is_pro,
                                                 profile_type=MastersProfile.TRAINER).exclude(
            id=current_profile.id).all()
        serialized = SelectProfileSerializer(profiles, many=True)
        return Response(serialized.data, status=status.HTTP_200_OK)

    @action(methods=['get'], detail=False)
    def get_profile(self, request, *args, **kwargs):
        user: User = request.user
        current_profile = user.masters_profile
        serialized = ProfileSerializer(current_profile)
        return Response(serialized.data, status=status.HTTP_200_OK)


class MoveViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Move.objects.all()
    serializer_class = MoveSerializer


class GameEventViewSet(viewsets.ModelViewSet):
    queryset = GameEvent.objects.all()
    serializer_class = GameEventSerializer

    @action(methods=['get'], detail=False)
    def list_available(self, request, *args, **kwargs):
        now_time = datetime.now()
        query = Q(available_date_from__gte=now_time, available_date_to__lte=now_time) | Q(force_available=True)
        events = GameEvent.objects.filter(query)
        serialized = GameEventSerializer(events, many=True)
        return Response(serialized.data, status=status.HTTP_200_OK)

    @action(methods=['get'], detail=True)
    def mod_file(self, request, pk=None, *args, **kwargs):
        trainer: Trainer = Trainer.get_from_user(request.user)
        event: GameEvent = GameEvent.objects.filter(GameEvent.get_available(), pk=pk).first()
        if event:
            mod_file = event.game_mod.get_mod_file_for_streamer(trainer.get_trainer_profile())
            return FileResponse(mod_file.file)
        return Response(status=status.HTTP_404_NOT_FOUND)


class WildcardViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Wildcard.objects.filter(is_active=True)
    serializer_class = WildcardSerializer
    permission_classes = [IsTrainer]

    @action(methods=['GET'], detail=False)
    def simplified(self, request, *args, **kwargs):
        serializer = SimplifiedWildcardSerializer(self.get_queryset(), many=True)
        return Response(serializer.data)

    @action(methods=['POST'], detail=True)
    def use_card(self, request, *args, **kwargs):
        wildcard: Wildcard = self.get_object()
        current_user = request.user
        fixed_user = current_user

        if current_user.masters_profile.profile_type == MastersProfile.COACH:
            return Response(data=dict(detail='coach_cant_use'), status=status.HTTP_400_BAD_REQUEST)

        quantity = int(request.data.get('quantity', 1))
        if wildcard.can_use(fixed_user, quantity):
            result = wildcard.use(fixed_user, quantity, **request.data)
            if result is True:
                return Response(data=dict(detail='card_used'), status=status.HTTP_200_OK)
            elif result is False:
                return Response(data=dict(detail='contact_paramada'), status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response(result, status=status.HTTP_200_OK)
        return Response(data=dict(detail='no_card_available'), status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['POST'], detail=True)
    def buy_card(self, request, *args, **kwargs):
        wildcard: Wildcard = self.get_object()
        quantity = int(request.data.get('quantity', 1))

        current_user = request.user
        fixed_user = current_user
        if current_user.masters_profile.profile_type == MastersProfile.COACH:
            return Response(data=dict(detail='coach_cant_buy'), status=status.HTTP_400_BAD_REQUEST)

        if wildcard.can_buy(fixed_user, quantity, True):
            if wildcard.buy(fixed_user, quantity, True):
                return Response(data=dict(detail='card_bought'), status=status.HTTP_200_OK)
            return Response(data=dict(detail='contact_paramada'), status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(data=dict(detail='no_enough_money'), status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['POST'], detail=True)
    def buy_and_use_card(self, request, *args, **kwargs):
        wildcard: Wildcard = self.get_object()
        quantity = int(request.data.get('quantity', 1))

        current_user = request.user
        fixed_user = current_user
        if current_user.masters_profile.profile_type == MastersProfile.COACH:
            return Response(data=dict(detail='coach_cant_use'), status=status.HTTP_400_BAD_REQUEST)

        if wildcard.can_buy(fixed_user, quantity):
            buyed = wildcard.buy(fixed_user, quantity)
            if buyed:
                used = wildcard.use(fixed_user, quantity, **request.data)
                if used is True:
                    return Response(data=dict(detail='card_bought_and_used', amount=buyed), status=status.HTTP_200_OK)
                elif used is False:
                    return Response(data=dict(detail='contact_paramada'), status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                return Response(used, status=status.HTTP_200_OK)
            return Response(data=dict(detail='contact_paramada'), status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(data=dict(detail='no_enough_money'), status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['GET'], detail=False)
    def list_strong_items(self, request, *args, **kwargs):
        from event_api.wildcards.handlers.give_strong_item import available_items as indexes
        items = Item.objects.filter(index__in=indexes)
        serializer = ItemSelectSerializer(items, many=True)
        return Response(serializer.data)

    @action(methods=['GET'], detail=False)
    def list_weak_items(self, request, *args, **kwargs):
        from event_api.wildcards.handlers.give_weak_item import available_items as indexes
        items = Item.objects.filter(index__in=indexes)
        serializer = ItemSelectSerializer(items, many=True)
        return Response(serializer.data)

    @action(methods=['GET'], detail=False)
    def list_mega_stones(self, request, *args, **kwargs):
        from event_api.wildcards.handlers.give_mega_item import mega_stones as indexes
        items = Item.objects.filter(index__in=indexes)
        serializer = ItemSelectSerializer(items, many=True)
        return Response(serializer.data)


def team_saver(team, trainer):
    new_version = TrainerTeam.objects.filter(trainer_old=trainer).count() + 1
    team_data = dict(
        version=new_version,
        trainer_old=trainer.pk,
        team=[pokemon for pokemon in team if pokemon]
    )

    new_team_serializer = TrainerTeamSerializer(data=team_data)
    if new_team_serializer.is_valid(raise_exception=True):
        new_team_obj = new_team_serializer.save()
        trainer.current_team = new_team_obj
        trainer.save()
        return True
    return False


def box_saver(boxes, trainer: Trainer):
    TrainerBox.objects.filter(trainer=trainer).delete()
    boxes_hash = dict()
    for box_num in range(7):
        boxes_hash[box_num] = TrainerBox.objects.create(box_number=box_num, trainer=trainer)

    for box_num, data in boxes.items():
        if not data:
            continue
        box_name = data['name']
        slots = data['slots']
        box = boxes_hash[box_num]
        box.name = box_name
        box.save()
        for slot in slots:
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
        from websocket.sockets import OverlayConsumer
        profile: MastersProfile = request.user.masters_profile
        file_obj = request.data['file'].file
        save_data = file_obj.read()
        file_obj.seek(0)
        trainer_name = get_trainer_name(save_data)

        if profile.trainer is None:
            if profile.profile_type == MastersProfile.TRAINER:
                trainer = Trainer.objects.create(name=trainer_name)
                profile.trainer = trainer
                profile.save()
            elif profile.profile_type == MastersProfile.COACH:
                trainer, _ = Trainer.objects.get_or_create(name=trainer_name)
                profile.trainer = trainer
                profile.save()

        trainer = profile.trainer

        data = dict(
            file=request.data['file'],
            trainer=trainer.pk
        )
        file_serializer = SaveFileSerializer(data=data)

        if file_serializer.is_valid():
            file_serializer.save()
            save_results = data_reader(save_data)
            trainer.gym_badge_1 = (save_results['badge_count'] & 0b00000001) != 0
            trainer.gym_badge_2 = (save_results['badge_count'] & 0b00000010) != 0
            trainer.gym_badge_3 = (save_results['badge_count'] & 0b00000100) != 0
            trainer.gym_badge_4 = (save_results['badge_count'] & 0b00001000) != 0
            trainer.gym_badge_5 = (save_results['badge_count'] & 0b00010000) != 0
            trainer.gym_badge_6 = (save_results['badge_count'] & 0b00100000) != 0
            trainer.gym_badge_7 = (save_results['badge_count'] & 0b01000000) != 0
            trainer.gym_badge_8 = (save_results['badge_count'] & 0b10000000) != 0
            trainer.save()
            team_saver(save_results.get('team'), trainer)
            box_saver(save_results.get('boxes'), trainer)
            OverlayConsumer.send_overlay_data(profile.streamer_name)
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


class LoadItemNamesView(APIView):
    permission_classes = [IsAuthenticated, IsRoot]

    def post(self, request, *args, **kwargs):
        for item in Item.objects.filter(index__gte=1, api_loaded=False):
            if item.name == '???':
                selector = item.index
            else:
                selector = item.name.lower().replace(" ", "-")
            url = f'https://pokeapi.co/api/v2/item/{selector}'
            response = requests.get(url)
            try:
                json_response = response.json()

                try:
                    new_es_localization, created = ItemNameLocalization.objects.get_or_create(
                        item=item, language='es',
                        defaults=dict(
                            content=list(filter(
                                lambda name:
                                name['language']['name'] == 'es',
                                json_response['names']))[0]['name']
                        ))
                    if created:
                        item.name_localizations.add(new_es_localization)
                    else:
                        new_es_localization.content = \
                            list(filter(lambda name: name['language']['name'] == 'es', json_response['names']))[0][
                                'name']
                        new_es_localization.save()
                except IndexError:
                    print(f'(es)translation not found for {item.name}#{item.index}')
                except KeyError:
                    raise ValueError(f'error finding data on {response.content} from url {url} @ {item.index}')

                try:
                    new_en_localization, created = ItemNameLocalization.objects.get_or_create(
                        item=item, language='en',
                        defaults=dict(
                            content=list(filter(
                                lambda name:
                                name['language']['name'] == 'en',
                                json_response['names']))[0]['name']
                        ))
                    if created:
                        item.name_localizations.add(new_en_localization)
                    else:
                        new_en_localization.content = \
                            list(filter(lambda name: name['language']['name'] == 'en', json_response['names']))[0][
                                'name']
                        new_en_localization.save()
                except IndexError:
                    print(f'(en)translation not found for {item.name}#{item.index}')
                except KeyError:
                    raise ValueError(f'error finding data on {response.content} from url {url} @ {item.index}')

            except requests.exceptions.JSONDecodeError:
                print(f'{response.content} for {item.index}')

            item.api_loaded = True
            item.save()
        return Response(status=status.HTTP_201_CREATED)


class NewsletterViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Newsletter.objects.all().order_by('-created_on')
    serializer_class = NewsletterSerializer
