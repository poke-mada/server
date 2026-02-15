from django.db import models
from django.db.models.functions import Lower


# Create your models here.

class ContextLocalization(models.Model):
    id = models.AutoField(primary_key=True, unique=True)
    language = models.CharField(max_length=2, db_index=True)
    extra = models.CharField(max_length=50, null=True, blank=True, db_index=True)
    content = models.TextField()

    def __str__(self):
        return f'{self.language} - {self.content}'


class ItemNameLocalization(models.Model):
    item = models.ForeignKey("Item", on_delete=models.CASCADE, db_column='item_id', related_name='name_localizations',
                             null=True)
    language = models.CharField(max_length=2, db_index=True, null=True, blank=False)
    content = models.TextField(null=True, blank=False)


class Item(models.Model):
    ITEM_BAGS = [
        ('berries', 'berries bag'),
        ('meds', 'meds bag'),
        ('tms', 'tms bag'),
        ('keys', 'keys bag'),
        ('items', 'items bag')
    ]
    id = models.AutoField(primary_key=True, unique=True)
    index = models.IntegerField()
    localization = models.CharField(max_length=2, db_index=True, default="en", null=True)
    flavor_text_localizations = models.ManyToManyField(ContextLocalization, blank=True,
                                                       related_name="item_flavor_texts")
    name = models.CharField(max_length=50)
    api_loaded = models.BooleanField(default=False)
    item_bag = models.CharField(max_length=100, null=True, blank=True, choices=ITEM_BAGS)
    custom_sprite = models.ImageField(upload_to='sprites/', null=True, blank=True)

    def __str__(self):
        return self.name


class Type(models.Model):
    id = models.AutoField(primary_key=True, unique=True)
    index = models.IntegerField()
    name_localizations = models.ManyToManyField(ContextLocalization, blank=True, related_name="type_names")
    flavor_text_localizations = models.ManyToManyField(ContextLocalization, blank=True,
                                                       related_name="type_flavor_texts")
    localization = models.CharField(max_length=2, db_index=True, default="en", null=True)
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class TypeCoverage(models.Model):
    id = models.AutoField(primary_key=True, unique=True)
    type_from = models.ForeignKey(Type, on_delete=models.CASCADE, related_name='coverages_from')
    type_to = models.ForeignKey(Type, on_delete=models.CASCADE, related_name='coverages_to')
    multiplier = models.DecimalField(max_digits=2, decimal_places=1)


class MoveCategory(models.Model):
    id = models.AutoField(primary_key=True, unique=True)
    index = models.IntegerField()
    name_localizations = models.ManyToManyField(ContextLocalization, blank=True)
    localization = models.CharField(max_length=2, db_index=True, default="en", null=True)
    name = models.CharField(max_length=15)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Move Categories"


class Move(models.Model):
    id = models.AutoField(primary_key=True, unique=True)
    index = models.IntegerField()
    localization = models.CharField(max_length=2, db_index=True, default="en", null=True)

    name_localizations = models.ManyToManyField(ContextLocalization, blank=True, related_name='move_names')
    flavor_text_localizations = models.ManyToManyField(ContextLocalization, blank=True,
                                                       related_name='move_flavor_texts')

    name = models.CharField(max_length=50)
    max_pp = models.IntegerField()
    move_type = models.ForeignKey(Type, on_delete=models.PROTECT)
    power = models.IntegerField()
    accuracy = models.IntegerField()
    category = models.ForeignKey(MoveCategory, on_delete=models.PROTECT, null=True)
    flavor_text = models.TextField()
    contact_flag = models.BooleanField(default=False)

    @property
    def double_damage_to(self):
        return self.move_type.coverages_from.filter(multiplier=2).values_list(Lower('type_to__name'), flat=True)

    @property
    def half_damage_to(self):
        return self.move_type.coverages_from.filter(multiplier=0.5).values_list(Lower('type_to__name'), flat=True)

    @property
    def no_damage_to(self):
        return self.move_type.coverages_from.filter(multiplier=0).values_list(Lower('type_to__name'), flat=True)

    def __str__(self):
        return self.name


class PokemonAbility(models.Model):
    id = models.AutoField(primary_key=True, unique=True)
    index = models.IntegerField()
    localization = models.CharField(max_length=2, db_index=True, default="en", null=True)
    name = models.CharField(max_length=50)
    flavor_text = models.TextField(default='')

    name_localizations = models.ManyToManyField(ContextLocalization, blank=True, related_name="ability_names")
    flavor_text_localizations = models.ManyToManyField(ContextLocalization, blank=True,
                                                       related_name='ability_flavor_texts')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Pokemon Abilities"


class PokemonNature(models.Model):
    STATS = [
        ('ATTACK', 'ATTACK',),
        ('DEFENSE', 'DEFENSE',),
        ('SPECIAL_ATTACK', 'SPECIAL ATTACK',),
        ('SPECIAL_DEFENSE', 'SPECIAL DEFENSE',),
        ('SPEED', 'SPEED')
    ]
    id = models.AutoField(primary_key=True, unique=True)
    index = models.IntegerField()
    name = models.CharField(max_length=50)
    localization = models.CharField(max_length=2, db_index=True, default="en", null=True)
    name_localizations = models.ManyToManyField(ContextLocalization, blank=True)

    stat_up = models.CharField(max_length=50, choices=STATS, validators=[], null=True, blank=True)
    stat_down = models.CharField(max_length=50, choices=STATS, validators=[], null=True, blank=True)

    def __str__(self):
        return self.name


class Pokemon(models.Model):
    id = models.AutoField(primary_key=True, unique=True)
    dex_number = models.IntegerField()
    name = models.CharField(max_length=50)
    form = models.CharField(max_length=20, default="0")
    types = models.ManyToManyField(Type)
    sprite = models.ImageField(upload_to='media/pokemon_sprites/')

    def __str__(self):
        return self.name

    def surrogate(self):
        from event_api.models import Evolution
        dex_numbers = Evolution.search_evolution_chain(self.dex_number)
        if 133 in dex_numbers:
            return [self]

        dex_numbers = Evolution.search_evolution_chain(self.dex_number)

        return Pokemon.objects.filter(dex_number__in=dex_numbers)

    def surrogate_dex(self):
        from event_api.models import Evolution
        dex_numbers = Evolution.search_evolution_chain(self.dex_number)

        if 133 in dex_numbers:
            return [self.dex_number]

        dex_numbers = Evolution.search_evolution_chain(self.dex_number)

        return dex_numbers

    class Meta:
        verbose_name_plural = 'Pokemon'
        constraints = (
            models.UniqueConstraint(
                fields=['dex_number', 'form'], name='form_dex_number'
            ),
        )
