from django.db import models
from django.utils.safestring import mark_safe

# Create your models here.


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True, null=True)

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"

    def __str__(self):
        return self.name



class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name="Категория")
    name = models.CharField(max_length=200, verbose_name="Название")
    subtitle = models.CharField(max_length=150, verbose_name="Подзаголовок", default='Велюр, массив кедра, индивидуальный размер.')
    is_from = models.BooleanField(default=False, verbose_name="от")
    is_green = models.BooleanField(default=False, verbose_name="зеленый ценник")
    price = models.IntegerField(verbose_name="Цена")
    main_image = models.ImageField(upload_to='products/', blank=True, null=True, verbose_name="Картинка")
    is_new = models.BooleanField(default=False, verbose_name="Новинка")

    material = models.CharField(max_length=255, verbose_name="Материал", default='Массив кедра, Велюр')
    production_time = models.CharField(max_length=100, verbose_name="Срок изготовления", default='от 22 дней')
    dimensions = models.CharField(max_length=100, verbose_name="Габариты", default='19000 x 1400 x 950 мм')
    description = models.TextField(verbose_name="Описание", default='Изысканный диван ручной работы. Мы используем только экологичные материалы. Возможен выбор цвета ткани под ваш интерьер.')

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
    image = models.ImageField(upload_to='products/extra/', verbose_name="Доп. фото")
    
    def image_tag(self):
        if self.image:
            # mark_safe говорит Django: "Это не опасный текст, это картинка, рисуй её!"
            return mark_safe(f'<img src="{self.image.url}" width="100" style="border-radius: 8px;"/>')
        return "Нет фото"
    
    image_tag.short_description = 'Предпросмотр'

    def __str__(self):
        # Считаем, сколько фоток у этого продукта имеют ID меньше или равный текущему
        count = self.product.images.filter(id__lte=self.id).count()
        return f"Фото №{count} для {self.product.name}"
        


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