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
    
class CategoryAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False
    def has_delete_permission(self, request, obj=None):
        return False



admin.site.register(Category, CategoryAdmin)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    # # Добавляем вкладыш с фотками в карточку товара
    # inlines = [ProductImageInline]
    # # Если хочешь видеть в списке товаров еще и категорию:
    # list_display = ('name', 'category')
    # # Выводим тег картинки в список полей, которые нельзя редактировать руками
    # readonly_fields = ('main_image_tag',)
    # # Определяем порядок полей, чтобы картинка была в самом верху
    # fields = ('main_image_tag', 'main_image', 'name', 'category', 'price')

    # 1. Список всех товаров (в таблице)
    list_display = ('main_image_tag', 'name', 'category', 'price', 'is_from', 'is_green', 'is_new')
    list_filter = ('category', 'is_new', 'is_green') # Фильтры справа
    list_editable = ('price', 'is_from', 'is_green', 'is_new') # Можно менять прямо в списке!
    
    # 2. Карточка самого товара (внутри)
    readonly_fields = ('main_image_tag',)
    
    fieldsets = (
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
