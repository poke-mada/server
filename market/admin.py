from django.contrib import admin

from admin_panel.admin import staff_site
from market.models import MarketPost, MarketSlot, BankedAsset, MarketPostOffer, MarketTransaction, MarketAlert


# Register your models here.

@admin.action(description="Perform Transactions")
def perform_transactions(modeladmin, request, queryset):
    for obj in queryset:
        obj.perform_transaction(force_transaction=True)


class MarketSlotPostInline(admin.TabularInline):
    readonly_fields = ['offer']
    model = MarketSlot
    extra = 0
    min_num = 1


class MarketSlotOfferInline(admin.TabularInline):
    readonly_fields = ['post']
    model = MarketSlot
    extra = 0
    min_num = 1


@admin.register(MarketPost, site=staff_site)
class MarketPostAdmin(admin.ModelAdmin):
    list_display = ('creator', 'status')
    inlines = [MarketSlotPostInline]


@admin.register(MarketPostOffer, site=staff_site)
class MarketPostOfferAdmin(admin.ModelAdmin):
    list_display = ('creator', 'status')
    inlines = [MarketSlotOfferInline]


@admin.register(BankedAsset, site=staff_site)
class BankedAssetAdmin(admin.ModelAdmin):
    list_display = ('user', 'content_type', 'quantity')


@admin.register(MarketTransaction, site=staff_site)
class MarketTransactionAdmin(admin.ModelAdmin):
    list_display = ('created_on', 'source__creator', 'source', 'target', 'target__creator')
    readonly_fields = ['created_on']
    actions = [perform_transactions]


staff_site.register(MarketAlert)
