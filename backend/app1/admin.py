from django.contrib import admin
from django import forms
from .models import Category, Product, Setting, ProductImage, SEO, FAQItem
from django.contrib.contenttypes.admin import GenericTabularInline

class ProductImageInline(admin.TabularInline):
    model = ProductImage  # Та самая модель, которую ты добавишь в models.py
    extra = 1             # Сколько пустых полей для новых фоток будет сразу
    # Добавляем наше превью в список полей
    readonly_fields = ('image_tag',)
    # Чтобы превью стояло первым, можно явно указать порядок полей:
    fields = ('image_tag', 'image')


class FAQItemAdminForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Если поле product есть в форме, отрубаем ему весь сопутствующий интерфейс
        if 'product' in self.fields:
            widget = self.fields['product'].widget
            widget.can_add_related = False     # Сносит плюс (+)
            widget.can_change_related = False  # Сносит карандаш
            widget.can_delete_related = False  # Сносит крестик
            widget.can_view_related = False    # Сносит глаз (если он был)


@admin.register(FAQItem)
class FAQItemAdmin(admin.ModelAdmin):
    list_display = ('question', 'page', 'product', 'url_path', 'order')
    list_filter = ('page', 'product')
    search_fields = ('question', 'answer')
    list_editable = ('page', 'product', 'url_path', 'order')

    def get_changelist_form(self, request, **kwargs):
        return FAQItemAdminForm
    
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
        'category_image_tag', 'category_image', 'category_slug', 'name', ('show_on_main', 'show_on_catalog', 'is_active')
    )


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    # 1. Список всех товаров (в таблце)
    list_display = ('main_image_tag', 'name', 'product_slug', 'category', 'price', 'is_from', 'is_green', 'is_new', 'is_active')
    list_filter = ('category', 'is_new', 'is_green', 'is_active') # Фильтры справа
    list_editable = ('price', 'is_from', 'is_green', 'is_new', 'is_active') # Можно менять прямо в списке!
    
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
            'fields': ('category', ('name', 'is_active'), 'subtitle')
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

    inlines = [ProductImageInline]

