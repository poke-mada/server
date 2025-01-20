from django.db import models
from django.db.models.functions import Lower


# Create your models here.

class ContextLocalization(models.Model):
    id = models.AutoField(primary_key=True, unique=True)
    language = models.CharField(max_length=2, db_index=True)
    content = models.TextField()

    def __str__(self):
        return f'{self.language} - {self.content}'

class Item(models.Model):
    id = models.AutoField(primary_key=True, unique=True)
    index = models.IntegerField()
    localization = models.CharField(max_length=2, db_index=True, default="en", null=True)
    name_localizations = models.ManyToManyField(ContextLocalization, blank=True, related_name="item_names")
    flavor_text_localizations = models.ManyToManyField(ContextLocalization, blank=True, related_name="item_flavor_texts")
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class Type(models.Model):
    id = models.AutoField(primary_key=True, unique=True)
    index = models.IntegerField()
    name_localizations = models.ManyToManyField(ContextLocalization, blank=True, related_name="type_names")
    flavor_text_localizations = models.ManyToManyField(ContextLocalization, blank=True, related_name="type_flavor_texts")
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
    flavor_text_localizations = models.ManyToManyField(ContextLocalization, blank=True, related_name='move_flavor_texts')

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

    name_localizations = models.ManyToManyField(ContextLocalization, blank=True, related_name="ability_names")
    flavor_text_localizations = models.ManyToManyField(ContextLocalization, blank=True, related_name='ability_flavor_texts')

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

    stat_up = models.CharField(max_length=50, choices=STATS, validators=[])
    stat_down = models.CharField(max_length=50, choices=STATS, validators=[])

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

    class Meta:
        verbose_name_plural = 'Pokemon'
        constraints = (
            models.UniqueConstraint(
                fields=['dex_number', 'form'], name='form_dex_number'
            ),
        )
