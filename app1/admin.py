from django.contrib import admin
from .models import Category, Product, Setting

class SettingAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return not Setting.objects.exists()
    def has_delete_permission(self, request, obj=None):
        return False
    
class CategoryAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False
    def has_delete_permission(self, request, obj=None):
        return False 

admin.site.register(Category, CategoryAdmin)
admin.site.register(Product)
admin.site.register(Setting, SettingAdmin)
