from django.db import models
from django.utils.safestring import mark_safe
from pytils.translit import slugify
from django.core.validators import RegexValidator
from django.utils.deconstruct import deconstructible
from io import BytesIO
from django.core.files.base import ContentFile
from PIL import Image, ImageOps
import os
from pillow_heif import register_heif_opener

register_heif_opener()
# Create your models here.

slug_validator = RegexValidator(
    regex=r'^[a-z0-9-]+$',
    message="Слаг может содержать только латиницу, цифры и дефис (никаких пробелов и подчеркиваний!)"
)


@deconstructible
class GenerateUploadPath:
    def __init__(self, subfolder=""):
        # subfolder будет либо пустой "", либо "webp/"
        self.subfolder = subfolder

    def __call__(self, instance, filename):
        if hasattr(instance, 'product'):
            slug = instance.product.product_slug
        else:
            slug = instance.product_slug
        
        # Строим путь: products/slug/подпапка/файл
        return f'products/{slug}/{self.subfolder}{filename}'



class Category(models.Model):
    name = models.CharField(max_length=100)
    category_slug = models.SlugField(max_length=255, unique=True, blank=True, validators=[slug_validator])
    category_image = models.ImageField(upload_to='categories/', blank=True, null=True, verbose_name="Картинка")
    show_on_main = models.BooleanField(default=True, verbose_name="Показывать категорию на главной странице")
    show_on_catalog = models.BooleanField(default=True, verbose_name="Показывать категорию в каталоге")

    def save(self, *args, **kwargs):
        if not self.category_slug:
            # Если слаг пустой — транслитим имя
            self.category_slug = slugify(self.name)
        super().save(*args, **kwargs)

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
    main_image = models.ImageField(upload_to=GenerateUploadPath(), blank=True, null=True, verbose_name="Картинка")
    main_image_webp =  models.ImageField(upload_to=GenerateUploadPath(subfolder="webp/"), blank=True, null=True, verbose_name="Webp картинка")
    is_new = models.BooleanField(default=False, verbose_name="Новинка")

    material = models.CharField(max_length=255, verbose_name="Материал", default='Массив кедра, Велюр')
    production_time = models.CharField(max_length=100, verbose_name="Срок изготовления", default='от 22 дней')
    dimensions = models.CharField(max_length=100, verbose_name="Габариты", default='19000 x 1400 x 950 мм')
    description = models.TextField(verbose_name="Описание", default='Изысканный диван ручной работы. Мы используем только экологичные материалы. Возможен выбор цвета ткани под ваш интерьер.')


    def save(self, *args, **kwargs):
        if not self.product_slug:
            # Если слаг пустой — транслитим имя
            self.product_slug = slugify(self.name)
        super().save(*args, **kwargs)
        if self.main_image and not self.main_image_webp:
            with Image.open(self.main_image.path) as img:
                # Исправляем ориентацию (айфоны и т.д.)
                img = ImageOps.exif_transpose(img)
                
                # Конвертируем в WebP в памяти
                output = BytesIO()
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
    image = models.ImageField(upload_to=GenerateUploadPath(), verbose_name="Доп. фото")
    image_webp = models.ImageField(upload_to=GenerateUploadPath(subfolder="webp/"), blank=True, null=True, verbose_name="Доп. фото Webp")
    
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
        super().save(*args, **kwargs)

        # 2. Если оригинал загружен, а WebP-версии еще нет
        if self.image and not self.image_webp:
            with Image.open(self.image.path) as img:
                img = ImageOps.exif_transpose(img)
                
                output = BytesIO()
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
