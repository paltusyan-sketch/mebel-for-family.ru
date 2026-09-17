import os
import tarfile
import subprocess
from django import forms
from django.contrib import admin
from django.http import FileResponse, Http404
from django.urls import path
from django.conf import settings
from django.utils.safestring import mark_safe
from .models import Category, Product, Setting, ProductImage, SEO, FAQItem
from django.contrib.contenttypes.admin import GenericTabularInline


import os
import subprocess
import tarfile
from django.contrib import admin
from django.http import FileResponse, Http404
from django.urls import path
from django.conf import settings # ИМПОРТИРУЕМ НАСТРОЙКИ ДЖАНГО

def download_backup_view(request):
    if not request.user.is_staff:
        raise Http404("Доступ ограничен")

    archive_path = "/app/final_backup_manual.tar.gz"
    db_sql_path = "/app/backup_db.sql"
    media_path = "/app/media"

    # АВТО-ВЫТЯГИВАНИЕ ДАННЫХ ИЗ ТВОЕЙ КОНФИГУРАЦИИ ДЖАНГО
    # Джанга берет их из .env, так что тут всегда будут 100% правильные доступы
    db_config = settings.DATABASES['default']
    db_name = db_config['NAME']
    db_user = db_config['USER']
    db_password = db_config['PASSWORD']
    db_host = db_config.get('HOST', 'db') # Если хост не задан, берем стандартный 'db'

    # Формируем универсальную команду с реальными параметрами текущей базы
    cmd = (
        f"pg_dump -h {db_host} -U {db_user} -d {db_name} > {db_sql_path} && "
        f"tar -czf {archive_path} -C /app/ backup_db.sql media && "
        f"rm -f {db_sql_path}"
    )

    try:
        env = os.environ.copy()
        # Передаем РЕАЛЬНЫЙ пароль, под которым Джанга прямо сейчас работает с базой
        env["PGPASSWORD"] = db_password

        subprocess.run(cmd, shell=True, check=True, env=env)

        if os.path.exists(archive_path) and os.path.getsize(archive_path) > 0:
            
            # Создаем кастомный класс ответа, который сам удалит файл при закрытии
            class DeleteOnCloseFileResponse(FileResponse):
                def close(self):
                    super().close()
                    if os.path.exists(archive_path):
                        os.remove(archive_path)
            
            # Отдаем файл через наш надежный класс
            response = DeleteOnCloseFileResponse(open(archive_path, 'rb'), as_attachment=True, filename='backup.tar.gz')
            return response
        else:
            raise Http404("Не удалось сформировать архив.")

    except subprocess.CalledProcessError as e:
        raise Http404(f"Ошибка утилиты pg_dump/tar внутри контейнера: {e}. Проверь логи контейнера базы данных!")
    except Exception as e:
        raise Http404(f"Ошибка бэкапа: {e}")

    

# Регистрация URL (Твоя рабочая схема, которую ты оставил)
original_get_urls = admin.site.get_urls
def custom_get_urls():
    urls = original_get_urls()
    my_urls = [
        path('download-backup/', admin.site.admin_view(download_backup_view), name='download_backup'),
    ]
    return my_urls + urls
admin.site.get_urls = custom_get_urls


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
    # Встроенный метод Джанго, который выводит зелёную кнопку на страницу Настроек
    def changelist_view(self, request, extra_context=None):
        button_html = (
            "<h3>📦 Резервное копирование UralMeb</h3>"
            "<a href='/admin/download-backup/' style='"
            "display: inline-block; padding: 8px 16px; background: #177c3e; "
            "color: #fff; border-radius: 4px; text-decoration: none; font-weight: bold; margin-top: 5px;"
            "'>Скачать полный бэкап сайта (.tar.gz)</a>"
        )
        self.message_user(request, mark_safe(button_html))
        return super().changelist_view(request, extra_context=extra_context)


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

