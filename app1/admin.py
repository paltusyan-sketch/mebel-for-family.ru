from django.contrib import admin
from .models import Category, Product, Setting, ProductImage

class ProductImageInline(admin.TabularInline):
    model = ProductImage  # Та самая модель, которую ты добавишь в models.py
    extra = 1             # Сколько пустых полей для новых фоток будет сразу
    # Добавляем наше превью в список полей
    readonly_fields = ('image_tag',)
    # Чтобы превью стояло первым, можно явно указать порядок полей:
    fields = ('image_tag', 'image')



class SettingAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return not Setting.objects.exists()
    def has_delete_permission(self, request, obj=None):
        return False
    


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return True
    def has_delete_permission(self, request, obj=None):
        return True
    
    readonly_fields = ('category_image_tag',)
    
    fields = (
        'category_image_tag', 'category_image', 'category_slug', 'name', ('show_on_main', 'show_on_catalog')
    )


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    # 1. Список всех товаров (в таблце)
    list_display = ('main_image_tag', 'name', 'product_slug', 'category', 'price', 'is_from', 'is_green', 'is_new')
    list_filter = ('category', 'is_new', 'is_green') # Фильтры справа
    list_editable = ('price', 'is_from', 'is_green', 'is_new') # Можно менять прямо в списке!
    
    # 2. Карточка самого товара (внутри)
    readonly_fields = ('main_image_tag',)
    
    fieldsets = (
        ('SEO', {
            'fields': ('product_slug',)
        }),
        ('Визуал', {
            'fields': ('main_image_tag', 'main_image')
        }),
        ('Основная инфа', {
            'fields': ('category', 'name', 'subtitle')
        }),
        ('Ценник и статусы', {
            'fields': (('price', 'is_from'), ('is_green', 'is_new')) # В одну строку для компактности
        }),
        ('Характеристики', {
            'fields': ('material', 'production_time', 'dimensions')
        }),
        ('Описание', {
            'fields': ('description',),
        }),
    )

    inlines = [ProductImageInline]


admin.site.register(Setting, SettingAdmin)
