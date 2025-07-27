from django.db import models


# Create your models here.
class InventoryGiftQuerySequence(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    run_times = models.IntegerField(default=0)
    name = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    inventory_bundle = models.ForeignKey('rewards_api.RewardBundle', on_delete=models.CASCADE)
    targets = models.ManyToManyField('event_api.MastersProfile')

    def run(self):
        from rewards_api.models import StreamerRewardInventory
        for target in self.targets.all():
            inventory, is_created = StreamerRewardInventory.objects.get_or_create(reward_id=self.inventory_bundle_id, profile=target, defaults=dict(
                exchanges=0,
                is_available=True
            ))
            if not inventory.is_available:
                inventory.is_available = True
            inventory.save()
        self.run_times += 1
        self.save()
