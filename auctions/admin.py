from django.contrib import admin

from .models import User, Listing, Watch, Bid, Comment, Category, SiteConfiguration

# Register your models here.
class BidAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "listing", "value", "created_at")
    list_filter = ("listing",)
    search_fields = ("user__username", "listing__title")

class CommentAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "listing", "comment", "created_at")
    list_filter = ("listing",)
    search_fields = ("user__username", "comment")

class ListingAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "title", "category", "starting_value", "auction_active", "created_at")
    list_filter = ("auction_active", "category")
    search_fields = ("title", "description")

class WatchAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "listing")

class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name",)

class SiteConfigurationAdmin(admin.ModelAdmin):
    list_display = ("site_name", "currency_symbol", "contact_email")
    
    def has_add_permission(self, request):
        # Only allow one configuration instance (singleton)
        if self.model.objects.exists():
            return False
        return super().has_add_permission(request)
    
    def has_delete_permission(self, request, obj=None):
        return False

admin.site.register(Bid, BidAdmin)
admin.site.register(Comment, CommentAdmin)
admin.site.register(Listing, ListingAdmin)
admin.site.register(User)
admin.site.register(Watch, WatchAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(SiteConfiguration, SiteConfigurationAdmin)