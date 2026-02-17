


from app1.models import Product

for_change = Product.objects.exclude(name = "Кровать Main")

for i in for_change:
    i.subtitle = 'Велюр, массив кедра, индивидуальный размер.'
    i.material = 'Массив кедра, Велюр'
    i.production_time = 'от 22 дней'
    i.dimensions = '19000 x 1400 x 950 мм'
    i.description = 'Изысканный диван ручной работы. Мы используем только экологичные материалы. Возможен выбор цвета ткани под ваш интерьер.'
    i.save()