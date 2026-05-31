
from app1.models import Product

for_save = Product.objects.all()

for i in for_save:
    i.save()