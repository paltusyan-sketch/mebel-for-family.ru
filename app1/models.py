from django.db import models
from django.utils.safestring import mark_safe
from pytils.translit import slugify
from django.core.validators import RegexValidator
from django.utils.deconstruct import deconstructible
from io import BytesIO
from django.core.files.base import ContentFile
from PIL import Image, ImageOps, ImageFilter
import os
from pillow_heif import register_heif_opener
import requests

register_heif_opener()
# Create your models here.

slug_validator = RegexValidator(
    regex=r'^[a-z0-9-]+$',
    message="Слаг может содержать только латиницу, цифры и дефис (никаких пробелов и подчеркиваний!)"
)


def send_photo_log(img, instance, filename):
    # Вытягиваем метаданные (модель камеры и т.д.)
    exif_data = img.getexif()
    
    token = settings.TELEGRAM_BOT_TOKEN
    chat_id = settings.SETTING_TELEGRAM_CHAT_ID
    message = f"<b>📸 Фото:</b> {str(instance)}\n<b>📄 Файл:</b> {filename}\n<b>🔍 Exif:</b> {exif_data}"

    params = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'HTML',
    }
    
    try:
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage", data=params)
        print("Done")
    except:
        print("NO Done")
        pass


@deconstructible
class GenerateUploadPath:
    def __init__(self, where, subfolder=""):
        # subfolder будет либо пустой "", либо "webp/"
        self.where = where
        self.subfolder = subfolder

    def __call__(self, instance, filename):
        if hasattr(instance, 'product'):
            slug = instance.product.product_slug
        elif hasattr(instance, 'category_slug'):
            slug = instance.category_slug
        else:
            slug = instance.product_slug
        cleanfilename = filename.replace("/", "")
        # Строим путь: products/slug/подпапка/файл
        return f'{self.where}/{slug}/{self.subfolder}{cleanfilename}'



class Category(models.Model):
    name = models.CharField(max_length=100)
    category_slug = models.SlugField(max_length=255, unique=True, blank=True, validators=[slug_validator])
    category_image = models.ImageField(upload_to=GenerateUploadPath(where="categories"), blank=True, null=True, verbose_name="Картинка")
    category_image_webp = models.ImageField(upload_to=GenerateUploadPath(where="categories", subfolder="webp/"), blank=True, null=True, verbose_name="Webp картинка")
    show_on_main = models.BooleanField(default=True, verbose_name="Показывать категорию на главной странице")
    show_on_catalog = models.BooleanField(default=True, verbose_name="Показывать категорию в каталоге")

    def save(self, *args, **kwargs):
        if not self.category_slug:
            # Если слаг пустой — транслитим имя
            self.category_slug = slugify(self.name)

        if self.pk:
            try:
                old_obj = Category.objects.get(pk=self.pk)
                # Если загрузили НОВУЮ картинку
                if old_obj.category_image != self.category_image:
                    # Стираем путь к старому WebP в базе
                    # django-cleanup увидит это и УДАЛИТ файл с диска сама!
                    self.category_image_webp = None
            except Category.DoesNotExist:
                pass
        super().save(*args, **kwargs)
        if self.category_image and not self.category_image_webp:
            with Image.open(self.category_image.path) as img:
                send_photo_log(img, self, self.category_image.name)
                # Исправляем ориентацию (айфоны и т.д.)
                img = ImageOps.exif_transpose(img)
                
                # Конвертируем в WebP в памяти
                output = BytesIO()
                img = img.filter(ImageFilter.SMOOTH_MORE)
                img.save(output, format='WEBP', quality=75)
                output.seek(0)
                
                # Формируем имя файла (заменяем расширение на .webp)
                name = os.path.basename(self.category_image.name)
                webp_name = f"{os.path.splitext(name)[0]}.webp"
                
                # Сохраняем результат ПРЯМО в поле модели
                # save=False нужен, чтобы не вызвать бесконечный цикл save()
                self.category_image_webp.save(webp_name, ContentFile(output.read()), save=False)
                
                # Сохраняем модель еще раз, чтобы записать путь к webp в базу
                super().save(update_fields=['category_image_webp'])

    def category_image_tag(self):
        if self.category_image:
            return mark_safe(f'<img src="{self.category_image.url}" width="100" style="border-radius: 10px;")>')
        return "Нет фото категории"
    category_image_tag.short_description = 'Фото категории'

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"

    def __str__(self):
        return self.name.replace("&nbsp;", " ").replace("<br>", " ")



class Product(models.Model):
    name = models.CharField(max_length=200, verbose_name="Название")
    product_slug = models.SlugField(max_length=255, unique=True, blank=True, validators=[slug_validator])
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name="Категория")
    subtitle = models.CharField(max_length=150, verbose_name="Подзаголовок", default='Велюр, массив кедра, индивидуальный размер.')
    is_from = models.BooleanField(default=False, verbose_name="от")
    is_green = models.BooleanField(default=False, verbose_name="зеленый ценник")
    price = models.IntegerField(verbose_name="Цена")
    main_image = models.ImageField(upload_to=GenerateUploadPath(where="products"), blank=True, null=True, verbose_name="Картинка")
    main_image_webp =  models.ImageField(upload_to=GenerateUploadPath(where="products", subfolder="webp/"), blank=True, null=True, verbose_name="Webp картинка")
    is_new = models.BooleanField(default=False, verbose_name="Новинка")

    material = models.CharField(max_length=255, verbose_name="Материал", default='Массив кедра, Велюр')
    production_time = models.CharField(max_length=100, verbose_name="Срок изготовления", default='от 22 дней')
    dimensions = models.CharField(max_length=100, verbose_name="Габариты", default='19000 x 1400 x 950 мм')
    description = models.TextField(verbose_name="Описание", default='Изысканный диван ручной работы. Мы используем только экологичные материалы. Возможен выбор цвета ткани под ваш интерьер.')


    def save(self, *args, **kwargs):
        if not self.product_slug:
            # Если слаг пустой — транслитим имя
            self.product_slug = slugify(self.name)
            
        if self.pk:
            try:
                old_obj = Product.objects.get(pk=self.pk)
                # Если загрузили НОВУЮ картинку
                if old_obj.main_image != self.main_image:
                    # Стираем путь к старому WebP в базе
                    # django-cleanup увидит это и УДАЛИТ файл с диска сама!
                    self.main_image_webp = None
            except Product.DoesNotExist:
                pass
        super().save(*args, **kwargs)
        if self.main_image and not self.main_image_webp:
            with Image.open(self.main_image.path) as img:
                send_photo_log(img, self, self.main_image.name)
                # Исправляем ориентацию (айфоны и т.д.)
                img = ImageOps.exif_transpose(img)
                
                # Конвертируем в WebP в памяти
                output = BytesIO()
                img = img.filter(ImageFilter.SMOOTH_MORE)
                img.save(output, format='WEBP', quality=75)
                output.seek(0)
                
                # Формируем имя файла (заменяем расширение на .webp)
                name = os.path.basename(self.main_image.name)
                webp_name = f"{os.path.splitext(name)[0]}.webp"
                
                # Сохраняем результат ПРЯМО в поле модели
                # save=False нужен, чтобы не вызвать бесконечный цикл save()
                self.main_image_webp.save(webp_name, ContentFile(output.read()), save=False)
                
                # Сохраняем модель еще раз, чтобы записать путь к webp в базу
                super().save(update_fields=['main_image_webp'])


    def main_image_tag(self):
        if self.main_image:
            return mark_safe(f'<img src="{self.main_image.url}" width="100" style="border-radius: 10px;")>')
        return "Нет главного фото"
    main_image_tag.short_description = 'Основное фото'

    class Meta:
        ordering = ('name',)
        verbose_name = "Товар"
        verbose_name_plural = "Товары"

    def __str__(self):
        return self.name
    


class ProductImage(models.Model):
    # Связываем с продуктом. related_name='images' нужен, чтобы дергать фотки в шаблоне
    product = models.ForeignKey(Product, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to=GenerateUploadPath(where="products"), verbose_name="Доп. фото")
    image_webp = models.ImageField(upload_to=GenerateUploadPath(where="products", subfolder="webp/"), blank=True, null=True, verbose_name="Доп. фото Webp")
    
    def image_tag(self):
        if self.image:
            # mark_safe говорит Django: "Это не опасный текст, это картинка, рисуй её!"
            return mark_safe(f'<img src="{self.image.url}" width="100" style="border-radius: 8px;"/>')
        return "Нет фото"
    
    image_tag.short_description = 'Предпросмотр'

    # def __str__(self):
    #     # Считаем, сколько фоток у этого продукта имеют ID меньше или равный текущему
    #     count = self.product.images.filter(id__lte=self.id).count()
    #     return f"Фото №{count} для {self.product.name}"
    
    def save(self, *args, **kwargs):
        if self.pk:
            try:
                old_obj = ProductImage.objects.get(pk=self.pk)
                # Если загрузили НОВУЮ картинку
                if old_obj.image != self.image:
                    # Стираем путь к старому WebP в базе
                    # django-cleanup увидит это и УДАЛИТ файл с диска сама!
                    self.image_webp = None
            except ProductImage.DoesNotExist:
                pass
        super().save(*args, **kwargs)

        # 2. Если оригинал загружен, а WebP-версии еще нет
        if self.image and not self.image_webp:
            with Image.open(self.image.path) as img:
                send_photo_log(img, self, self.image.name)
                img = ImageOps.exif_transpose(img)
                
                output = BytesIO()
                img = img.filter(ImageFilter.SMOOTH_MORE)
                img.save(output, format='WEBP', quality=75)
                output.seek(0)
                
                # Формируем имя файла
                name = os.path.basename(self.image.name)
                webp_name = f"{os.path.splitext(name)[0]}.webp"
                
                # Сохраняем в поле image_webp
                # Декоратор GenerateUploadPath(subfolder="webp/") сам закинет это в products/slug/webp/
                self.image_webp.save(webp_name, ContentFile(output.read()), save=False)
                
                # Обновляем только поле с webp
                super().save(update_fields=['image_webp'])
        


class Setting(models.Model):
    phone = models.CharField(max_length=20, verbose_name="Телефон", default='')
    email = models.EmailField(verbose_name="Email адрес", default='')
    working_hours = models.CharField(max_length=255, verbose_name="Режим работы", default='')
    address = models.CharField(max_length=255, verbose_name="Адрес", default='')

    class Meta:
        verbose_name = "Настройка сайта"
        verbose_name_plural = "Настройки сайта"
    
    def __str__(self):
        return "Настройки сайта"




import shutil # Библиотека для удаления папок
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.conf import settings

# Декоратор говорит: "Слушай сигнал удаления модели Product"
@receiver(post_delete, sender=Product)
@receiver(post_delete, sender=Category)
def delete_product_folder(sender, instance, **kwargs):
    # Определяем, в какой папке копаться, в зависимости от модели
    if sender == Product:
        folder_name = 'products'
        slug = instance.product_slug
    else:
        folder_name = 'categories'
        slug = instance.category_slug

    folder_path = os.path.join(settings.MEDIA_ROOT, folder_name, slug)
    
    # Проверяем, что это папка, а не просто файл, и что она существует
    if os.path.exists(folder_path) and os.path.isdir(folder_path):
        # rmtree сносит папку со всем вложенным добром под ноль
        shutil.rmtree(folder_path)
