from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Restaurant, MenuCategory, MenuItem

@admin.register(Restaurant)
class RestaurantAdmin(UserAdmin):
    list_display = ['username', 'name', 'pan_number']
    fieldsets = UserAdmin.fieldsets + (
        ('Restaurant Info', {'fields': ('name', 'pan_number')}),
    )

@admin.register(MenuCategory)
class MenuCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'restaurant']
    list_filter = ['restaurant']

@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price']
    list_filter = ['category__restaurant', 'category']
    search_fields = ['name', 'description']
