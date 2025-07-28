from datetime import datetime

from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models import Q, Sum
from django.utils.safestring import mark_safe

from pokemon_api.scripting.save_reader import clamp
from trainer_data.models import Trainer
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

    def save(self, *args, **kwargs):
        new_ = super(CoinTransaction, self).save(*args, **kwargs)

        DataConsumer.send_custom_data(self.profile.user.username, dict(
            type='coins_notification',
            data=self.profile.economy
        ))

        return new_

    class Meta:
        verbose_name = 'Economy Log'
        verbose_name_plural = 'Economy Logs'


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
    extra_url = models.URLField(blank=True, null=True)
    always_available = models.BooleanField(default=False)  # models.py (dentro de Wildcard)
    handler_key = models.CharField(max_length=100, blank=True, null=True,
                                   help_text="Identificador del handler a usar (ej: 'give_item')")

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

    def can_buy(self, user: User, amount, force_buy=False):
        inventory, _ = user.streamer_profile.wildcard_inventory.get_or_create(wildcard=self, defaults=dict(quantity=0))

        already_in_possession = inventory.quantity
        if not force_buy:
            amount_to_buy = clamp(amount - already_in_possession, 0)
        else:
            amount_to_buy = amount
        return self.is_active and (
                (user.masters_profile.economy >= self.price * amount_to_buy) or self.always_available)

    def can_use(self, user: User, amount):
        streamer = user.masters_profile
        inventory: StreamerWildcardInventoryItem = streamer.wildcard_inventory.filter(wildcard=self).first()
        current_segment = user.masters_profile.current_segment_settings
        if self.category == Wildcard.OFFENSIVE and current_segment.karma < self.karma_consumption:
            # si es un comodin de ataque y no hay karma suficiente no puede usarse
            return 'cant_use'
        return (inventory and inventory.quantity >= amount) or self.always_available

    def buy(self, user: User, amount: int, force_buy=False):
        if not self.is_active:
            return False
        if self.always_available:
            return True
        inventory, _ = user.masters_profile.wildcard_inventory.get_or_create(wildcard=self, defaults=dict(quantity=0))

        already_in_possession = inventory.quantity
        if not force_buy:
            amount_to_buy = clamp(amount - already_in_possession, 0)
        else:
            amount_to_buy = amount

        if amount_to_buy == 0:
            return True

        CoinTransaction.objects.create(
            profile=user.masters_profile,
            amount=self.price * amount_to_buy,
            TYPE=CoinTransaction.OUTPUT,
            reason=f'se compró la carta {self.name}'
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

            if handler_cls:
                handler = handler_cls(self, user)
                context = {
                    'amount': amount,
                    **kwargs
                }
                handler.validate(context)
                result = handler.execute(context)
                WildcardLog.objects.create(wildcard=self, profile=profile,
                                           details=f'{amount} carta/s {self.name} usada')
                if result == 'cannot_attack':
                    return False
            else:
                # fallback default (log-only)
                result = True
                WildcardLog.objects.create(wildcard=self, profile=profile,
                                           details=f'{amount} wildcard(s) {self.name} used')
            if not self.always_available:
                inventory: StreamerWildcardInventoryItem = streamer.wildcard_inventory.filter(wildcard=self).first()
                inventory.quantity -= amount
                inventory.save()
            return result
        except Exception as e:
            import traceback
            ErrorLog.objects.create(
                profile=profile,
                details=f'{amount} wildcard(s) {self.name} tried to execute',
                message=traceback.format_exc()
            )
            return False


class WildcardLog(models.Model):
    profile = models.ForeignKey("MastersProfile", on_delete=models.CASCADE, related_name="wildcard_logs", null=True)
    trainer = models.ForeignKey(Trainer, on_delete=models.CASCADE, related_name='use_logs', null=True)
    wildcard = models.ForeignKey(Wildcard, on_delete=models.CASCADE, related_name='use_logs')
    details = models.TextField(blank=False, default="No details provided")


class StreamerWildcardInventoryItem(models.Model):
    profile = models.ForeignKey("MastersProfile", on_delete=models.CASCADE, related_name="wildcard_inventory",
                                null=True)
    wildcard = models.ForeignKey(Wildcard, on_delete=models.PROTECT)
    quantity = models.IntegerField(validators=[MinValueValidator(0)])

    def __str__(self):
        return f'x{self.quantity} {self.wildcard.name}'


class Streamer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="streamer_profile", null=True, blank=True)
    name = models.CharField(max_length=50, default="")

    def __str__(self):
        return self.name


class ProfilePlatformUrl(models.Model):
    profile = models.ForeignKey("MastersProfile", on_delete=models.CASCADE)
    platform = models.CharField(max_length=50)
    url = models.CharField(max_length=260)

    def __str__(self):
        return self.platform

    class Meta:
        verbose_name = "Social"
        verbose_name_plural = "Socials"


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
    streamer_name = models.CharField(max_length=50, default="", blank=False, null=True)
    coached = models.ForeignKey("MastersProfile", on_delete=models.SET_NULL, null=True, blank=True,
                                related_name="coaches")
    web_picture = models.ImageField(upload_to='profiles/web/', null=True, blank=False)
    trainer = models.ForeignKey(Trainer, on_delete=models.PROTECT, related_name="users", null=True, blank=True)
    profile_type = models.SmallIntegerField(choices=PROFILE_TYPES.items(), default=TRAINER)
    death_count = models.IntegerField(validators=[MinValueValidator(0)], default=0)
    rom_name = models.CharField(max_length=50, default="Pokémon X")
    is_pro = models.BooleanField(default=False)
    tournament_league = models.CharField(max_length=1, choices=LEAGUES.items(), default='-')
    save_path = models.CharField(max_length=260, null=True, blank=True,
                                 default=r'%APPDATA%\Lime3DS\sdmc\Nintendo 3DS\00000000000000000000000000000000\00000000000000000000000000000000\title\00040000\00055d00\data\00000001')
    is_tester = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {self.trainer.name if self.trainer else '-'} | {self.get_profile_type_display()}"

    @property
    def last_save(self):
        return self.trainer.saves.order_by('created_on').last().file.url

    @property
    def wildcard_count(self):
        return 0

    @property
    def current_segment_settings(self):
        return self.segments_settings.filter(is_current=True).first()

    def last_save_download(self):
        return mark_safe('<a href="{0}" download>Download {1} Save</a>'.format(self.last_save, self.trainer.name))

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
    available_community_skip = models.BooleanField(default=True, verbose_name="Skip de Comunidad Disponible")
    community_pokemon_id = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(821)],
                                               verbose_name="Pokemon de comunidad", null=True, blank=True)

    karma = models.DecimalField(validators=[MinValueValidator(0), MaxValueValidator(5)], default=1, decimal_places=1,
                                verbose_name="Karma", help_text="Capacidad de usar comodines de ataque fuerte",
                                max_digits=3)
    steal_karma = models.DecimalField(validators=[MinValueValidator(0), MaxValueValidator(5)], default=0,
                                      decimal_places=1, verbose_name="Karma de Robo Justo",
                                      help_text="Al juntar 3, se desbloquea \"Robo justo\"", max_digits=3)
    attacks_received_left = models.DecimalField(validators=[MinValueValidator(0), MaxValueValidator(4)],
                                                decimal_places=1, verbose_name="Experiencia", default=4,
                                                help_text="Ataques que puede recibir en el tramo", max_digits=3)
    shinies_freed = models.IntegerField(validators=[MinValueValidator(0)],
                                        help_text="Cuantos shinies ha liberado en el tramo", default=0,
                                        verbose_name="Shinies liberados")
    cure_lady_left = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(1)],
                                         help_text="Cuantos comodines de Dama de la Cura quedan en el tramo", default=1,
                                         verbose_name="Dama de la Cura restantes")
    death_count = models.IntegerField(validators=[MinValueValidator(0)], help_text="Muertes en un tramo", default=0,
                                      verbose_name="Conteo de muertes")
    tournament_league = models.CharField(max_length=1, choices=LEAGUES.items(), default='-', verbose_name="Liga",
                                         help_text="Liga a la que se llegó en este tramo")

    team = models.CharField

    # TODO: al final de tramo se borran escudo protector y reversa y todos los ofensivos medios y fuertes
    # TODO: escudo a seleccion, no automatico
    # TODO: 15 monedas -muertes de tramo

    def save(self, *args, **kwargs):
        if not self.pk:
            current_segment = self.profile.segments_settings.filter(is_current=True).first()
            if current_segment:
                self.tournament_league = current_segment.tournament_league

            self.profile.segments_settings.update(is_current=False)
        super().save(*args, **kwargs)

    @property
    def community_pokemon_sprite(self):
        return f'https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{self.community_pokemon_id}.png'

    class Meta:
        verbose_name = "Configuración de Tramo"
        verbose_name_plural = "Configuraciones de Tramo"


class LoaderThread(models.Model):
    thread_id = models.CharField(max_length=100, default="", blank=True)


class GameEvent(models.Model):
    available_date_from = models.DateTimeField()
    available_date_to = models.DateTimeField()
    force_available = models.BooleanField()

    def __str__(self):
        return f'{self.game_mod.mod_name}'

    def is_available(self):
        if self.force_available:
            return True
        now_time = datetime.now()
        return self.available_date_from <= now_time <= self.available_date_to

    @staticmethod
    def get_available():
        now_time = datetime.now()
        return Q(force_available=True) | Q(available_date_from__gte=now_time, available_date_to__lte=now_time)


class GameMod(models.Model):
    event = models.OneToOneField(GameEvent, on_delete=models.PROTECT, related_name="game_mod", null=True)
    mod_file = models.FileField(upload_to='mods/', null=False)
    mod_name = models.CharField(max_length=50, blank=False)
    mod_description = models.TextField(blank=True, null=True)

    def save(self, *args, **kwargs):
        return super().save(*args, **kwargs)


class DeathLog(models.Model):
    profile = models.ForeignKey(MastersProfile, on_delete=models.CASCADE, related_name="deaths", null=True)
    trainer = models.ForeignKey(Trainer, on_delete=models.CASCADE, related_name="death_log")
    created_on = models.DateTimeField(auto_now_add=True)
    died_in = models.CharField(max_length=100)
    pid = models.CharField(max_length=100)
    species_name = models.CharField(max_length=100)
    mote = models.CharField(max_length=100)

    class Meta:
        unique_together = ("profile", "species_name")


class MastersSegment(models.Model):
    end_date = models.DateTimeField()
    delimiter_key = models.CharField(max_length=100, blank=True, null=True,
                                     help_text="Identificador del handler a usar (ej: 'second_badge')")
    name = models.CharField(max_length=100)


class Imposter(models.Model):
    message = models.CharField(max_length=100, unique=True, help_text="texto en MINUSCULAS para encontrar al impostor")
    coin_reward = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(99)])


class ProfileImposterLog(models.Model):
    profile = models.ForeignKey(MastersProfile, on_delete=models.CASCADE, related_name="imposters")
    imposter = models.ForeignKey(Imposter, on_delete=models.SET_NULL, null=True)
    created_on = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.pk:
            CoinTransaction.objects.create(
                profile=self.profile,
                amount=self.imposter.coin_reward,
                reason=f'encontrado {self.imposter.message}',
                TYPE=CoinTransaction.INPUT
            )
        super().save(*args, **kwargs)


class Newsletter(models.Model):
    created_on = models.DateTimeField(auto_now_add=True)
    message = models.TextField()
