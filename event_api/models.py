from datetime import datetime
import uuid
import random
from typing import Union

import boto3
from botocore.config import Config
from django.conf import settings
from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models, transaction
from django.db.models import Q, Sum
from django.utils.safestring import mark_safe
from django.utils import timezone

from pokemon_api.models import Pokemon
from pokemon_api.scripting.save_reader import clamp
from rewards_api.models import RewardBundle, StreamerRewardInventory, Reward
from trainer_data.models import Trainer, TrainerPokemon, TrainerBox
from websocket.sockets import DataConsumer


# Create your models here.
class SaveFile(models.Model):
    accessible = models.BooleanField(default=False)
    trainer = models.ForeignKey(Trainer, on_delete=models.CASCADE, related_name='saves')
    file = models.FileField(upload_to='saves/')
    created_on = models.DateTimeField(auto_now_add=True, null=True)


class ErrorLog(models.Model):
    profile = models.ForeignKey("MastersProfile", on_delete=models.CASCADE, related_name='errors', null=True,
                                blank=False)
    trainer = models.ForeignKey(Trainer, on_delete=models.SET_NULL, null=True)
    details = models.TextField(null=True, blank=True)
    message = models.TextField(null=True, blank=False)


class CoinTransaction(models.Model):
    INPUT = 0
    OUTPUT = 1
    TRANSACTION_TYPES = (
        (INPUT, 'Ingreso'),
        (OUTPUT, 'Egreso')
    )
    profile = models.ForeignKey("MastersProfile", on_delete=models.CASCADE, related_name='transactions', null=True,
                                blank=False)
    amount = models.IntegerField()
    reason = models.TextField(blank=False, default="No reason provided")
    TYPE = models.SmallIntegerField(choices=TRANSACTION_TYPES, default=INPUT)
    created_on = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    segment = models.IntegerField(default=1)

    def save(self, *args, **kwargs):
        obj = super(CoinTransaction, self).save(*args, **kwargs)
        DataConsumer.send_custom_data(self.profile.user.username, dict(
            type='coins_notification',
            data=self.profile.economy
        ))

        return obj

    class Meta:
        verbose_name = 'Transaccion'
        verbose_name_plural = 'Registro de Economia'


class Wildcard(models.Model):
    AESTETHICAL = 0
    HEAL = 1
    PROTECT = 2
    STAT_BOOST = 3
    ITEMS = 4
    CAPTURE = 5
    OFFENSIVE = 6
    ECONOMY = 7
    CHALLENGE = 8
    CHOSEN_ONE = 9

    QUALITIES = (
        (AESTETHICAL, 'Esteticos'),
        (HEAL, 'Curacion'),
        (PROTECT, 'Protección'),
        (STAT_BOOST, 'Boosteos'),
        (ITEMS, 'Items'),
        (CAPTURE, 'Captura'),
        (OFFENSIVE, 'Ataque'),
        (ECONOMY, 'Economía'),
        (CHALLENGE, 'Retos'),
        (CHOSEN_ONE, 'El Elegido'),
    )

    LOW = 0
    MID = 1
    STRONG = 2

    ATTACK_LEVELS = (
        (LOW, 'Bajo/Especial'),
        (MID, 'Medio'),
        (STRONG, 'Fuerte'),
    )

    name = models.CharField(max_length=500, blank=False)
    price = models.IntegerField(validators=[MinValueValidator(-1)], null=True, blank=True)
    special_price = models.CharField(max_length=500, null=True, blank=True)
    sprite = models.ImageField(upload_to='wildcards/', null=True, blank=False)
    description = models.TextField(blank=False, default="")
    category = models.SmallIntegerField(choices=QUALITIES, default=AESTETHICAL, verbose_name="Categoría")
    attack_level = models.SmallIntegerField(choices=ATTACK_LEVELS, default=LOW, verbose_name="Nivel de Ataque",
                                            help_text="Nivel de Ataque solo para comodines de ATAQUE")
    is_active = models.BooleanField(default=True)
    is_wip = models.BooleanField(default=False, verbose_name="Esta en desarrollo")
    extra_url = models.URLField(blank=True, null=True)
    always_available = models.BooleanField(default=False)  # models.py (dentro de Wildcard)
    segment_available = models.IntegerField(default=0)
    handler_key = models.CharField(max_length=100, blank=True, null=True,
                                   help_text="Identificador del handler a usar (ej: 'give_item')")
    noob_price = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return self.name

    @property
    def karma_consumption(self):
        if self.attack_level == Wildcard.STRONG and self.category == Wildcard.OFFENSIVE:
            return 1

        if self.attack_level == Wildcard.MID and self.category == Wildcard.OFFENSIVE:
            return 0

        if self.attack_level == Wildcard.LOW and self.category == Wildcard.OFFENSIVE:
            return 0
        return 0

    @property
    def sprite_name(self):
        return self.sprite.name

    def get_price(self, user: User):
        profile = user.masters_profile

        if not profile.is_pro and self.noob_price:
            return self.noob_price

        if self.name.lower() == 'robo justo' or self.id == 53:
            return self.price

        return self.price

    def can_buy(self, user: User, amount, force_buy=False):
        profile = user.masters_profile
        inventory, _ = profile.wildcard_inventory.get_or_create(wildcard=self, defaults=dict(quantity=0))

        if not profile.current_segment_settings or profile.current_segment_settings.cure_lady_left <= 0 and (
                self.id == 9 or self.name.lower() == 'dama de la cura'):
            return 'No puedes comprar mas damas de la cura'

        if (profile.current_segment_settings and not profile.current_segment_settings.justice_steal_bought) and (
                self.id == 53 or self.name.lower() == 'robo justo'):
            return 'No puedes comprar mas Robos Justos'

        already_in_possession = inventory.quantity
        if not force_buy:
            amount_to_buy = clamp(amount - already_in_possession, 0)
        else:
            amount_to_buy = amount
        return self.is_active and (
                (profile.economy >= self.get_price(user) * amount_to_buy) or self.always_available)

    def can_use(self, user: User, amount, **data):
        from event_api.wildcards.registry import get_executor

        profile = user.masters_profile
        inventory: StreamerWildcardInventoryItem = profile.wildcard_inventory.filter(wildcard=self).order_by(
            '-quantity').first()

        if inventory and inventory.quantity < amount and not self.always_available:
            return False

        handler_cls = get_executor(self.handler_key)
        if handler_cls:
            handler = handler_cls(self, user)
            context = {
                'amount': amount,
                **data
            }
            validation = handler.validate(context)
            if isinstance(validation, str):
                return validation

        return True

    def buy(self, user: User, amount: int, force_buy=False):
        if not self.is_active:
            return False
        if self.always_available:
            return True
        inventory, _ = user.masters_profile.wildcard_inventory.get_or_create(wildcard=self, defaults=dict(quantity=0))

        amount_to_buy = amount

        if amount_to_buy == 0:
            return True

        if self.id == 9 or self.name.lower() == 'dama de la cura':
            css = user.masters_profile.current_segment_settings
            css.cure_lady_left -= 1
            css.save()

        if self.id == 53 or self.name.lower() == 'robo justo':
            css = user.masters_profile.current_segment_settings
            css.justice_steal_bought = False
            css.save()

        CoinTransaction.objects.create(
            profile=user.masters_profile,
            amount=self.get_price(user) * amount_to_buy,
            TYPE=CoinTransaction.OUTPUT,
            segment=user.masters_profile.current_segment_settings.segment,
            reason=f'se compró la carta {self.name}'
        )

        WildcardUpdateLog.objects.create(
            profile=user.masters_profile,
            message=f'Se ha comprado el comodin {self.name} {amount_to_buy} vez/veces'
        )

        inventory.quantity += amount_to_buy
        inventory.save()
        return amount_to_buy

    def use(self, user: User, amount: int, **kwargs):
        from event_api.wildcards.registry import get_executor

        profile: MastersProfile = user.masters_profile
        try:
            streamer = user.masters_profile
            handler_cls = get_executor(self.handler_key)

            if not handler_cls:
                return 'El comodin no ha sido configurado'
            handler = handler_cls(self, user)
            context = {
                'amount': amount,
                **kwargs
            }
            result = handler.execute(context)
            WildcardLog.objects.create(wildcard=self, profile=profile,
                                       details=f'{amount} carta/s {self.name} usada')

            if not self.always_available:
                inventory: StreamerWildcardInventoryItem = streamer.wildcard_inventory.filter(wildcard=self).first()
                inventory.quantity -= amount
                inventory.save()
            return result
        except Exception as e:
            import traceback
            error = ErrorLog.objects.create(
                profile=profile,
                details=f'{amount} wildcard(s) {self.name} tried to execute',
                message=traceback.format_exc()
            )
            return f'error: {error.id}'

    class Meta:
        verbose_name = "Comodín"
        verbose_name_plural = "Comodines"


class WildcardLog(models.Model):
    profile = models.ForeignKey("MastersProfile", on_delete=models.CASCADE, related_name="wildcard_logs", null=True)
    wildcard = models.ForeignKey(Wildcard, on_delete=models.CASCADE, related_name='use_logs')
    details = models.TextField(blank=False, default="No details provided")

    class Meta:
        verbose_name = "Registro de comodin"
        verbose_name_plural = "Registro de comodines"


class StreamerWildcardInventoryItem(models.Model):
    profile = models.ForeignKey("MastersProfile", on_delete=models.CASCADE, related_name="wildcard_inventory",
                                null=True)
    wildcard = models.ForeignKey(Wildcard, on_delete=models.PROTECT)
    quantity = models.IntegerField(validators=[MinValueValidator(0)])

    def __str__(self):
        return f'x{self.quantity} {self.wildcard.name}'


class ProfilePlatformUrl(models.Model):
    profile = models.ForeignKey("MastersProfile", on_delete=models.CASCADE)
    platform = models.CharField(max_length=50)
    url = models.CharField(max_length=260)

    def __str__(self):
        return self.platform

    class Meta:
        verbose_name = "Social"
        verbose_name_plural = "Socials"


class BannedPokemon(models.Model):
    profile = models.ForeignKey("MastersProfile", on_delete=models.CASCADE, related_name="banned_mons")
    dex_number = models.IntegerField()
    species_name = models.CharField(max_length=50)
    reason = models.TextField(blank=True)

    class Meta:
        verbose_name = "Pokemon Baneado"
        verbose_name_plural = "Pokemon Baneados"


class MastersProfile(models.Model):
    TRAINER = 0
    COACH = 1
    ADMIN = 2

    PROFILE_TYPES = {
        TRAINER: 'Trainer',
        COACH: 'Coach',
        ADMIN: 'Admin',
    }

    LEAGUES = {
        '-': '------',
        'A': 'Liga A',
        'B': 'Liga B',
        'C': 'Liga C',
        'D': 'Liga D',
        'E': 'Liga E'
    }

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="masters_profile")
    streamer_name = models.CharField(max_length=50, default="", blank=False, null=True,
                                     verbose_name="Nombre de Streamer")
    coached = models.ForeignKey("MastersProfile", on_delete=models.SET_NULL, null=True, blank=True,
                                related_name="coaches", verbose_name='Ahijado')
    main_coach = models.ForeignKey("MastersProfile", on_delete=models.SET_NULL, null=True, blank=True,
                                   verbose_name='Coach principal')
    starter_dex_number = models.IntegerField(null=True, blank=True, verbose_name="Pokémon \"El Elegido\"")
    in_pokemon_league = models.BooleanField(default=False, verbose_name="Dentro de la liga")
    already_won_lysson = models.BooleanField(default=False, verbose_name="Le ganó a Lysson")
    description = models.TextField(null=True, blank=True, verbose_name="Descripción")
    web_picture = models.ImageField(upload_to='profiles/web/', null=True, blank=True, verbose_name="Foto Perfil")
    trainer = models.ForeignKey(Trainer, on_delete=models.PROTECT, related_name="users", null=True, blank=True,
                                verbose_name="Entrenador")
    wipe_clause_available = models.BooleanField(default=True, verbose_name="Clausula de Wipeo Disponible")
    profile_type = models.SmallIntegerField(choices=PROFILE_TYPES.items(), default=TRAINER,
                                            verbose_name="Tipo de Perfil")
    death_count = models.IntegerField(validators=[MinValueValidator(0)], default=0,
                                      verbose_name="Conteo de muertes totales")
    death_count_display = models.IntegerField(validators=[MinValueValidator(0)], default=0,
                                              verbose_name="Conteo de muertes totales para overlay")
    rom_name = models.CharField(max_length=50, default="Pokémon ORAS", verbose_name="Nombre de Rom")
    event_joined_id = models.IntegerField(null=True, blank=True, verbose_name="Evento iniciado")
    is_pro = models.BooleanField(default=False, verbose_name="Es pro?")
    tournament_league = models.CharField(max_length=1, choices=LEAGUES.items(), default='-', verbose_name="Liga")
    save_path = models.CharField(max_length=260, null=True, blank=True,
                                 default=r'%APPDATA%\Lime3DS\sdmc\Nintendo 3DS\00000000000000000000000000000000\00000000000000000000000000000000\title\00040000\00055d00\data\00000001')
    is_tester = models.BooleanField(default=False, verbose_name="Es Tester?")
    has_animated_overlay = models.BooleanField(default=False, verbose_name='Overlay Animado')
    showdown_token = models.OneToOneField("admin_panel.ShowdownToken", null=True, blank=True,
                                          verbose_name="Token para showdown", on_delete=models.SET_NULL)
    gym_2_save = models.FileField(upload_to='profile/saves/', null=True, blank=True)
    gym_3_save = models.FileField(upload_to='profile/saves/', null=True, blank=True)
    gym_4_save = models.FileField(upload_to='profile/saves/', null=True, blank=True)
    gym_5_save = models.FileField(upload_to='profile/saves/', null=True, blank=True)
    gym_6_save = models.FileField(upload_to='profile/saves/', null=True, blank=True)
    gym_7_save = models.FileField(upload_to='profile/saves/', null=True, blank=True)
    gym_8_save = models.FileField(upload_to='profile/saves/', null=True, blank=True)

    def __str__(self):
        return self.streamer_name or f"U:{self.user.username}"

    @property
    def death_count_display_f(self):
        return self.segments_settings.aggregate(total_deaths=Sum('death_count_display'))['total_deaths']

    @property
    def last_save(self):
        return self.trainer.saves.order_by('created_on').last().file

    def get_last_releasable_by_dex_number(self, dex_number, source_stealer: "MastersProfile" = None):
        if source_stealer:
            banned_mons = BannedPokemon.objects.filter(Q(profile=source_stealer) | Q(profile=self)).values_list(
                'dex_number', flat=True
            ).distinct()
        else:
            banned_mons = BannedPokemon.objects.filter(profile=self).values_list('dex_number', flat=True)

        death_mons = DeathLog.objects.exclude(
            dex_number__in=banned_mons
        ).filter(
            profile=self,
            revived=False
        ).values_list('dex_number', flat=True)

        starter_tree = Evolution.search_evolution_chain(self.starter_dex_number)
        greninja_tree = Evolution.search_evolution_chain(658)

        last_version = TrainerPokemon.objects.exclude(
            pokemon__dex_number__in=banned_mons
        ).exclude(
            pokemon__dex_number__in=greninja_tree,
            mote__iexact='greninja-ash'
        ).exclude(
            pokemon__dex_number__in=death_mons
        ).exclude(
            pokemon__dex_number__in=starter_tree
        ).filter(
            trainer=self.trainer
        ).filter(
            pokemon__dex_number=dex_number
        ).last()

        return last_version

    def give_wildcard(self, wildcard: Wildcard, quantity: int = 1, notification: str = "Te ha llegado un comodín!"):

        bundle = RewardBundle.objects.create(
            name=notification,
            user_created=True
        )

        Reward.objects.create(
            reward_type=Reward.WILDCARD,
            bundle=bundle,
            quantity=quantity,
            wildcard=wildcard
        )

        StreamerRewardInventory.objects.create(
            profile=self.user.masters_profile,
            reward=bundle
        )

        DataConsumer.send_custom_data(self.user.username, dict(
            type='notification',
            data='Te ha llegado un paquete al buzón!'
        ))

        ProfileNotification.objects.create(
            profile=self.user.masters_profile,
            message='Te ha llegado un paquete al buzón!'
        )

    def get_last_pokemon_by_dex_number(self, dex_number):

        boxed_mons = TrainerBox.objects.filter(
            trainer=self.trainer
        ).values_list('slots__pokemon__pokemon__dex_number', flat=True)

        last_version = TrainerPokemon.objects.filter(
            Q(team__trainer=self.trainer) |
            Q(pokemon__dex_number__in=boxed_mons, trainerboxslot__isnull=False,
              trainerboxslot__box__trainer=self.trainer),
            pokemon__dex_number=dex_number
        ).last()

        return last_version

    def get_last_stealable_by_dex_number(self, profile, dex_number):
        robbed_banned_mons = BannedPokemon.objects.filter(profile=self).values_list('dex_number', flat=True)
        robber_banned_mons = BannedPokemon.objects.filter(profile=profile).values_list('dex_number', flat=True)
        robber_already_captured = []

        robbed_death_mons = DeathLog.objects.exclude(
            dex_number__in=robbed_banned_mons
        ).filter(
            profile=self, revived=False
        ).values_list('dex_number', flat=True)

        robber_death_mons = DeathLog.objects.exclude(
            dex_number__in=robbed_banned_mons
        ).filter(
            profile=self, revived=False
        ).values_list('dex_number', flat=True)

        boxed_mons = TrainerBox.objects.filter(trainer=self.trainer).values_list('slots__pokemon__pokemon__dex_number',
                                                                                 flat=True)

        last_version = TrainerPokemon.objects.exclude(
            Q(pokemon__dex_number__in=robbed_banned_mons) |
            Q(pokemon__dex_number__in=[658, self.starter_dex_number]) |
            Q(pokemon__dex_number__in=robbed_death_mons) |
            Q(pokemon__dex_number__in=robber_death_mons) |
            Q(pokemon__dex_number__in=robber_banned_mons) |
            Q(pokemon__dex_number__in=robber_already_captured)
        ).filter(
            Q(team__trainer=self.trainer) |
            Q(pokemon__dex_number__in=boxed_mons, trainerboxslot__isnull=False,
              trainerboxslot__box__trainer=self.trainer)
        ).filter(pokemon__dex_number=dex_number).last()

        return last_version

    @property
    def wildcard_count(self):
        return 0

    @property
    def current_segment_settings(self) -> Union["MastersSegmentSettings", None]:
        if self.profile_type == MastersProfile.COACH:
            if self.coached:
                return self.coached.segments_settings.filter(is_current=True).first()
            return None
        return self.segments_settings.filter(is_current=True).first()

    def last_save_download(self):
        presigned_url = cache.get(f'cached_save_for_profile_{self.pk}')
        if not presigned_url:
            import os
            STORAGE_TIMEOUT = 60 * 15
            file_field = self.last_save
            s3_key = file_field.name  # Ej: "prod/media/documentos/archivo.pdf"
            ENVIRONMENT = os.getenv("DJANGO_ENV", "prod")  # "dev", "stage" o "prod"
            full_s3_path = os.path.join(ENVIRONMENT, 'dedsafio-pokemon/media', s3_key)
            s3 = boto3.client(
                's3',
                region_name='us-east-1',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                config=Config(signature_version='s3v4', s3={"use_accelerate_endpoint": True})
            )
            presigned_url = s3.generate_presigned_url(
                'get_object',
                Params={'Bucket': settings.AWS_STORAGE_BUCKET_NAME, 'Key': full_s3_path},
                ExpiresIn=STORAGE_TIMEOUT,
            )
            cache.set(f'cached_save_for_profile_{self.pk}', presigned_url,
                      timeout=STORAGE_TIMEOUT)  # Cache for 15 minutes
        return mark_safe('<a href="{0}" download>Download {1} Save</a>'.format(presigned_url, self.trainer.name))

    def has_wildcard(self, wildcard: "Wildcard") -> bool:
        if self.current_segment_settings:
            if wildcard.pk == 53 and self.current_segment_settings.steal_karma < 3:
                return False

        return self.wildcard_inventory.filter(wildcard=wildcard, quantity__gte=1).exists()

    def consume_wildcard(self, wildcard: "Wildcard", quantity: int = 1) -> bool:
        if self.current_segment_settings:
            if wildcard.pk == 53 and self.current_segment_settings.steal_karma < 3:
                return False
        inventory: StreamerWildcardInventoryItem = self.wildcard_inventory.filter(wildcard=wildcard,
                                                                                  quantity__gte=1).first()
        inventory.quantity -= quantity
        inventory.save()
        return True

    def has_shield(self) -> bool:
        return self.wildcard_inventory.filter(wildcard__handler_key='escudo_protector', quantity__gte=1).exists()

    def has_reverse(self) -> bool:
        return self.wildcard_inventory.filter(wildcard__handler_key='reverse_handler', quantity__gte=1).exists()

    @property
    def economy(self):
        if self.profile_type == MastersProfile.ADMIN:
            return 999

        if self.profile_type == MastersProfile.TRAINER:
            inputs = self.transactions.filter(
                TYPE=CoinTransaction.INPUT
            ).aggregate(Sum('amount'))['amount__sum'] or 0

            outputs = self.transactions.filter(
                TYPE=CoinTransaction.OUTPUT
            ).aggregate(Sum('amount'))['amount__sum'] or 0

            return inputs - outputs

        return None

    def has_item(self, banked_asset, quantity):
        agg_total_quantity = self.banked_assets.filter(
            content_type=banked_asset.content_type,
            object_id=banked_asset.object_id,
            trade_locked=False
        ).aggregate(Sum('quantity'))['quantity__sum'] or 0
        if banked_asset.content_type.model == 'trainerpokemon':
            if quantity > 1:
                return False
        return agg_total_quantity >= quantity


class MastersSegmentSettings(models.Model):
    LEAGUES = {
        '-': '------',
        'A': 'Liga A',
        'B': 'Liga B',
        'C': 'Liga C',
        'D': 'Liga D',
        'E': 'Liga E'
    }

    profile = models.ForeignKey(MastersProfile, on_delete=models.CASCADE, related_name="segments_settings", null=True,
                                blank=True)
    is_current = models.BooleanField(default=True, verbose_name="Tramo Actual")
    segment = models.IntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(99)],
                                  verbose_name="Tramo")
    community_skip_used_in = models.CharField(max_length=255, verbose_name="Skip de Comunidad en", null=True,
                                              blank=True)
    available_community_skip = models.BooleanField(default=True, verbose_name="Skip de Comunidad Disponible")
    community_pokemon_id = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(821)],
                                               verbose_name="Pokemon de comunidad", null=True, blank=True)

    karma = models.DecimalField(validators=[MinValueValidator(0), ], default=1, decimal_places=1,
                                verbose_name="Karma", help_text="Capacidad de usar comodines de ataque fuerte",
                                max_digits=9)
    steal_karma = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(settings.MAX_EXPERIENCE)],
                                      default=0, verbose_name="Karma de Robo Justo",
                                      help_text="Al juntar 3, se desbloquea \"Robo justo\"")
    attacks_received = models.IntegerField(validators=[MinValueValidator(0)], default=0,
                                           verbose_name="Ataques Recibidos",
                                           help_text="Ataques que ha recibido en el tramo")
    shinies_freed = models.IntegerField(validators=[MinValueValidator(0)],
                                        help_text="Cuantos shinies ha liberado en el tramo", default=0,
                                        verbose_name="Shinies liberados")
    cure_lady_left = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(1)],
                                         help_text="Cuantos comodines de Dama de la Cura quedan en el tramo", default=1,
                                         verbose_name="Dama de la Cura restantes")
    death_count = models.IntegerField(validators=[MinValueValidator(0)], help_text="Muertes en un tramo", default=0,
                                      verbose_name="Conteo de muertes")
    death_count_display = models.IntegerField(validators=[MinValueValidator(0)],
                                              help_text="Muertes en el tramo del overlay", default=0)
    tournament_league = models.CharField(max_length=1, choices=LEAGUES.items(), default='-', verbose_name="Liga",
                                         help_text="Liga a la que se llegó en este tramo")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creacion", null=True)
    finished_at = models.DateTimeField(null=True, verbose_name="Fecha de Finalizacion de tramo", blank=True)
    justice_steal_bought = models.BooleanField(default=False, verbose_name="Robo justo comprado")
    team = models.CharField

    def __str__(self):
        return f'Tramo {self.segment}'

    def save(self, *args, **kwargs):
        if self.pk:
            return super().save(*args, **kwargs)

        # a partir de aqui solo es tramo nuevo
        current_segment: "MastersSegmentSettings" = self.profile.segments_settings.filter(
            is_current=True).first()  # busca el tramo actual antes de crear el nuevo

        if not current_segment:
            return super().save(*args, **kwargs)
        # aqui siempre hay tramos anteriores, asi que hay que definirlos como no actuales

        current_segment.finished_at = timezone.now()
        current_segment.save()

        money_amount = clamp(15 - current_segment.death_count, 0, 15)
        current_settigns: SegmentConfiguration = SegmentConfiguration.objects.filter(segment=current_segment.segment,
                                                                                     is_tournament=False).first()
        if current_segment.finished_at < current_settigns.ends_at:
            money_amount = 0

        CoinTransaction.objects.create(
            profile=self.profile,
            TYPE=CoinTransaction.INPUT,
            amount=money_amount,
            segment=self.profile.current_segment_settings.segment,
            reason=f'Se han dado {money_amount} monedas por terminar el tramo con {current_segment.death_count} muertes el {current_segment.finished_at}'
        )

        self.profile.wildcard_inventory.filter(
            wildcard__category__in=[Wildcard.PROTECT, Wildcard.OFFENSIVE]
        ).exclude(
            wildcard__category=Wildcard.OFFENSIVE,
            wildcard__attack_level=Wildcard.LOW
        ).update(quantity=0)

        for reward in self.profile.reward_inventory.filter(is_available=True,
                                                           reward__user_created=True):  # type: StreamerRewardInventory
            if reward.reward.rewards.filter(wildcard__category=Wildcard.OFFENSIVE).exists():
                reward.is_available = False
                reward.save()

        self.tournament_league = current_segment.tournament_league
        self.profile.segments_settings.update(is_current=False)

        if self.profile.get_last_pokemon_by_dex_number(self.community_pokemon_id):
            # si el pokemon de la comunidad fue capturado, lo demas da igual
            return super().save(*args, **kwargs)

        # Busca toda la rama evolutiva y la banea
        community_pokemon = Pokemon.objects.filter(dex_number=self.community_pokemon_id).first()

        if community_pokemon:
            pokemons = community_pokemon.surrogate()
        else:
            pokemons = []

        if not TrainerPokemon.objects.filter(trainer=self.profile.trainer, pokemon__in=pokemons).exists():
            for pokemon in pokemons:
                BannedPokemon.objects.create(
                    profile=self.profile,
                    dex_number=self.community_pokemon_id,
                    species_name=pokemon.name,
                    reason=f'Pokemon de la comunidad sin capturar'
                )

        return super().save(*args, **kwargs)

    @property
    def community_pokemon_sprite(self):
        return f'https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{self.community_pokemon_id}.png'

    class Meta:
        verbose_name = "Configuración de Tramo"
        verbose_name_plural = "Configuraciones de Tramo"


class LoaderThread(models.Model):
    thread_id = models.CharField(max_length=100, default="", blank=True)


class GameEvent(models.Model):
    SEGMENT = 'Tramo'
    INGAME = 'Juego'

    COMBAT = 'Combate'
    SPECIAL = 'Especial'
    CAPTURE = 'Captura'

    EVENT_TYPES = {
        SEGMENT: 'Tramo',
        INGAME: 'Juego'
    }
    EVENT_SUBTYPES = {
        COMBAT: 'Combate',
        SPECIAL: 'Especial',
        CAPTURE: 'Captura'
    }

    type = models.CharField(max_length=100, choices=EVENT_TYPES.items(), default=INGAME, blank=True)
    sub_type = models.CharField(max_length=100, choices=EVENT_SUBTYPES.items(), default=COMBAT, blank=True)
    available_date_from = models.DateTimeField(verbose_name="Disponible desde el")
    available_date_to = models.DateTimeField(verbose_name="Disponible hasta el")
    force_available = models.BooleanField()
    testers_only = models.BooleanField(default=False)
    free_join = models.BooleanField(default=False)
    only_for_noobs = models.BooleanField(default=False)
    name = models.CharField(max_length=100, null=True, blank=False)
    description = models.TextField(null=True, blank=False, verbose_name="Descripcion")
    requirements = models.TextField(null=True, blank=False, verbose_name="Requisitos")
    reward_bundle = models.ForeignKey(RewardBundle, on_delete=models.PROTECT, null=True, blank=True,
                                      verbose_name="Preset de recompensa")
    text_reward = models.TextField(null=True, blank=True, verbose_name="Recompensa especial")

    def __str__(self):
        return f'{self.name}'

    def rewards(self):
        if not self.reward_bundle:
            return []
        return self.reward_bundle.rewards

    @property
    def is_available(self):
        if self.force_available:
            return True
        now_time = timezone.now()
        return self.available_date_from <= now_time <= self.available_date_to

    @property
    def can_join(self):
        if self.type == GameEvent.SEGMENT:
            return False

        if self.free_join:
            return self.is_available

        if self.is_available:
            now_time = timezone.now()
            return now_time < self.available_date_from

        return False

    @staticmethod
    def get_available(profile: MastersProfile):
        now_time = timezone.now()

        if profile.is_tester:
            events = GameEvent.objects.filter(
                Q(force_available=True) | Q(available_date_from__lte=now_time, available_date_to__gte=now_time) | Q(
                    id=profile.event_joined_id)
            ).order_by('available_date_to')
        else:
            events = GameEvent.objects.filter(
                Q(force_available=True) | Q(available_date_from__lte=now_time, available_date_to__gte=now_time) | Q(
                    id=profile.event_joined_id),
                testers_only=False
            ).order_by('available_date_to')

        if profile.is_pro:
            events = events.filter(only_for_noobs=False)

        return events

    class Meta:
        verbose_name = "Evento"
        verbose_name_plural = "Eventos"


class GameMod(models.Model):
    event = models.OneToOneField(GameEvent, on_delete=models.PROTECT, related_name="game_mod", null=True)
    mod_file = models.FileField(upload_to='mods/', null=False)
    mod_name = models.CharField(max_length=50, blank=False)
    mod_description = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Mod"
        verbose_name_plural = "Mods"


class DeathLog(models.Model):
    profile = models.ForeignKey(MastersProfile, on_delete=models.CASCADE, related_name="deaths", null=True)
    created_on = models.DateTimeField(auto_now_add=True)
    dex_number = models.IntegerField(null=True, blank=False)
    species_name = models.CharField(max_length=100)
    mote = models.CharField(max_length=100)
    segment = models.IntegerField(null=True, blank=False, default=1)
    revived = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.species_name:
            from pokemon_api.models import Pokemon
            self.species_name = Pokemon.objects.filter(dex_number=self.dex_number).first().name
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Acta de Defunción"
        verbose_name_plural = "Registro de muertes"


class MastersSegment(models.Model):
    end_date = models.DateTimeField()
    delimiter_key = models.CharField(max_length=100, blank=True, null=True,
                                     help_text="Identificador del handler a usar (ej: 'second_badge')")
    name = models.CharField(max_length=100)


class Imposter(models.Model):
    message = models.CharField(max_length=100, unique=True, help_text="texto en MINUSCULAS para encontrar al impostor")
    segment = models.IntegerField(default=1, verbose_name="Tramo")
    coin_reward = models.IntegerField(default=1,
                                      help_text='Maxima cantidad de monedas a obtener (SIN CONTAR A LOS PRIMEROS 10)')

    def __str__(self):
        return self.message

    class Meta:
        verbose_name = "Impostor"
        verbose_name_plural = "Impostores"


class ProfileImposterLog(models.Model):
    profile = models.ForeignKey(MastersProfile, on_delete=models.CASCADE, related_name="imposters",
                                verbose_name="Jugador")
    imposter = models.ForeignKey(Imposter, on_delete=models.SET_NULL, null=True, verbose_name='Impostor')
    registered_amount = models.IntegerField(default=0, null=True, blank=True, verbose_name='Monedas Registradas')
    created_on = models.DateTimeField(auto_now_add=True)

    @transaction.atomic
    def save(self, *args, **kwargs):
        if not self.pk:
            min_value = 1
            max_value = self.imposter.coin_reward
            same_cateogry_profiles = MastersProfile.objects.filter(
                is_pro=self.profile.is_pro,
                is_tester=self.profile.is_tester
            ).values_list("id", flat=True)

            first_10 = ProfileImposterLog.objects.filter(
                imposter=self.imposter,
                profile_id__in=same_cateogry_profiles
            ).count() < 10

            if first_10:
                min_value = 2
                max_value = self.imposter.coin_reward + 1

            self.registered_amount = random.randint(min_value, max_value)

            CoinTransaction.objects.create(
                profile=self.profile,
                amount=self.registered_amount,
                segment=self.profile.current_segment_settings.segment,
                reason=f'encontrado {self.imposter.message}',
                TYPE=CoinTransaction.INPUT
            )
        super().save(*args, **kwargs)

    class Meta:
        unique_together = ['profile', 'imposter']


class Newsletter(models.Model):
    ALL = 0
    PROS = 1
    NOOBS = 2
    TARGET = 3

    TARGETS = {
        ALL: 'Todos',
        PROS: 'Pros',
        NOOBS: 'Noobs',
        TARGET: 'Seleccionado'
    }

    created_on = models.DateTimeField(auto_now_add=True)
    message = models.TextField(verbose_name='Mensaje')
    target_method = models.SmallIntegerField(choices=TARGETS, default=ALL, verbose_name='Objetivos de envío')
    targets = models.ManyToManyField('event_api.MastersProfile', blank=True, verbose_name='Objetivos Seleccionados')
    send_notification = models.BooleanField(default=False, verbose_name='Enviar Notificacion')
    run_on_save = models.BooleanField(default=False, verbose_name='Ejecutar al guardar')

    def save(self, *args, **kwargs):
        obje = super().save(*args, **kwargs)

        if not self.run_on_save:
            return obje

        queryset = MastersProfile.objects.all()

        if self.target_method == Newsletter.ALL:
            queryset = MastersProfile.objects.all()
        elif self.target_method == Newsletter.PROS:
            queryset = MastersProfile.objects.filter(is_pro=True, is_tester=False)
        elif self.target_method == Newsletter.NOOBS:
            queryset = MastersProfile.objects.filter(is_pro=False, is_tester=False)
        elif self.target_method == Newsletter.TARGET:
            queryset = self.targets.all()

        if self.send_notification:
            for profile in queryset:
                DataConsumer.send_custom_data(profile.user.username, dict(
                    type='alert-notification',
                    data=self.message
                ))
                if self.target_method == Newsletter.TARGET:
                    ProfileNotification.objects.create(
                        profile=profile,
                        message=self.message
                    )

        self.run_on_save = False

        return super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Noticia"
        verbose_name_plural = "Tablon de Noticias"


class StealLog(models.Model):
    created_on = models.DateTimeField(auto_now_add=True)
    source = models.CharField(max_length=50)
    target = models.CharField(max_length=50)
    pokemon = models.CharField(max_length=50)
    bundle = models.ForeignKey(RewardBundle, on_delete=models.PROTECT, null=True)


class Evolution(models.Model):
    dex_number = models.IntegerField(db_index=True)
    root_evolution = models.IntegerField(db_index=True)

    def get_pokemon(self):
        return Pokemon.objects.get(dex_number=self.dex_number)

    def surrogate(self):
        evolution_chain = Evolution.objects.filter(root_evolution=self.root_evolution).values_list('dex_number',
                                                                                                   flat=True)

        return evolution_chain

    @staticmethod
    def search_evolution_chain(dex_number: int):
        evolution = Evolution.objects.filter(dex_number=dex_number).first()
        if evolution:
            return evolution.surrogate()
        else:
            return [evolution]


class ProfileNotification(models.Model):
    profile = models.ForeignKey(MastersProfile, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


class Sanction(models.Model):
    profile = models.ForeignKey(MastersProfile, on_delete=models.CASCADE, related_name='sanctions')
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    money_substracted = models.IntegerField(default=0, validators=[MinValueValidator(0)])

    def save(self, *args, **kwargs):
        Newsletter.objects.create(
            message=self.message,
            target_method=Newsletter.ALL,
        )

        ProfileNotification.objects.create(
            profile=self.profile,
            message=self.message
        )

        DataConsumer.send_custom_data(self.profile.user.username, dict(
            type='notification',
            data=self.message
        ))

        CoinTransaction.objects.create(
            profile=self.profile,
            reason=self.message,
            TYPE=CoinTransaction.OUTPUT,
            segment=self.profile.current_segment_settings.segment,
            amount=self.money_substracted
        )

        return super().save(*args, **kwargs)

    class Meta:
        verbose_name_plural = 'Sanciones'
        verbose_name = 'Sancion'


class WildcardUpdateLog(models.Model):
    profile = models.ForeignKey(MastersProfile, on_delete=models.CASCADE, related_name='wildcard_update_logs')
    message = models.TextField()

    class Meta:
        verbose_name_plural = 'Registros de inventario de comodines'
        verbose_name = 'Registro de inventario de comodin'


class SegmentConfiguration(models.Model):
    segment = models.IntegerField(default=1)
    is_tournament = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()

    class Meta:
        verbose_name_plural = 'Configuraciones de tramo'
        verbose_name = 'Configuracion de tramo'


class AlreadyCapturedLog(models.Model):
    profile = models.ForeignKey(MastersProfile, on_delete=models.CASCADE, related_name='captures')
    dex_number = models.IntegerField(null=True)
    pid = models.CharField(max_length=15)
    created_at = models.DateTimeField(auto_now_add=True)
