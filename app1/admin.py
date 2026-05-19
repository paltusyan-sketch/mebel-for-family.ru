from django.contrib import admin
from .models import Category, Product, Setting, ProductImage, SEO, FAQItem
from django.contrib.contenttypes.admin import GenericTabularInline

class ProductImageInline(admin.TabularInline):
    model = ProductImage  # Та самая модель, которую ты добавишь в models.py
    extra = 1             # Сколько пустых полей для новых фоток будет сразу
    # Добавляем наше превью в список полей
    readonly_fields = ('image_tag',)
    # Чтобы превью стояло первым, можно явно указать порядок полей:
    fields = ('image_tag', 'image')

# 1. Создаем универсальный инлайн
class FAQItemGenericInline(GenericTabularInline):
    model = FAQItem
    extra = 1
    fields = ['question', 'answer', 'order']


@admin.register(FAQItem)
class FAQItemAdmin(admin.ModelAdmin):
    list_display = ('question', 'page', 'product', 'url_path', 'order')
    list_filter = ('page', 'product')
    search_fields = ('question', 'answer')
    
    # Группируем поля, чтобы они разделялись визуальными блоками
    fieldsets = (
        ('Контент вопроса', {
            'fields': ('question', 'answer', 'order')
        }),
        ('Вариант 1: Привязка к разделу', {
            'fields': ('page',),
        }),
        ('Вариант 2: Привязка к товару', {
            'fields': ('product',),
        }),
        ('Вариант 3: Кастомная привязка по ссылке', {
            'fields': ('url_path',),
        }),
    )


@admin.register(Setting)
class SettingAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return not Setting.objects.exists()
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(SEO)
class SEOAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return not SEO.objects.exists()
    def has_delete_permission(self, request, obj=None):
        return False
    
    fieldsets = (
        ('/main/', {
            'fields': ('main_title', 'main_description', 'main_h1')
        }),
        ('/catalog/', {
            'fields': ('catalog_title', 'catalog_description', 'catalog_h1')
        }),
        ('/contacts/', {
            'fields': ('contacts_title', 'contacts_description', 'contacts_h1')
        }),
        ('/projects/', {
            'fields': ('projects_title', 'projects_description', 'projects_h1')
        }),
        ('/policy/', {
            'fields': ('policy_title', 'policy_description', 'policy_h1')
        }),
    )
    
    

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return True
    def has_delete_permission(self, request, obj=None):
        if obj is None:
            return True
        if not obj.show_on_main and not obj.show_on_catalog:
            return True
        return False
    
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
    readonly_fields = ('main_image_tag', 'og_image_tag')
    
    fieldsets = (
        ('SEO', {
            'fields': ('product_slug', 'seo_title', 'seo_description')
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
        ('OG', {
            'fields': ('og_title', 'og_description', 'og_image_tag', 'og_image')
        }),
    )

    # inlines = [FAQItemGenericInline]

