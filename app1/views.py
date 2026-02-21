import requests
from django.http import HttpResponse
from django.conf import settings
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from .models import Product
from .forms import OrderForm

# Create your views here.

def send_telegram_notification(data, is_spam=False):
    if data['comment']:
        comment = f"\nКомментарий: <b>{data['comment']}</b>"
    else:
        comment = ""

    raw_phone = data['phone'].replace(' ', '').replace('(', '').replace(')', '').replace('-', '')
    message = f"{'СПАМ !!!\n\n' if is_spam else ""}Имя: <b>{data['name']}</b>\nТелефон: <b>{raw_phone}</b>" + comment

    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    params = {
        'chat_id': settings.TELEGRAM_CHAT_ID,
        'text': message,
        'parse_mode': 'HTML',
        'disable_notification': is_spam,
    }
    response = requests.post(url, data=params)
    



def index_page(request):
    # Если данные отправлены методом POST
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if request.POST.get('imail') or request.POST.get('honeypot'):
            form.is_valid()
            send_telegram_notification(form.cleaned_data, True)
            messages.error(request, 'Система распосзнала, что вы бот!')
            return redirect('main')
        if form.is_valid():
            send_telegram_notification(form.cleaned_data)
            messages.success(request, 'Ваша заявка успешно отправлена!')
            return redirect('main') # Перенаправляем на ту же страницу
    else:
        # Если метод GET, создаем пустую форму
        form = OrderForm()

    context = {'form': form}
    return render(request, "index.html", context)


def catalog_page(request, category_slug=None):
    
    if category_slug:
        products = Product.objects.filter(category__slug=category_slug)
        context = {
            'products': products
        }
    else:
        all_products = Product.objects.all()
        context = {
            'products': all_products
        }

    return render(request, "catalog.html", context)


def product_page(request, category_slug, product_id):
    product = get_object_or_404(
        Product, 
        id=product_id,
        category__slug=category_slug # Дополнительная проверка для безопасности
    )

    context = {'product' : product}
    return render(request, "product.html", context)


def contacts_page(request):
    initial_data = {}
    product_id = request.GET.get('product_id')

    if product_id:
        try:
            # Находим продукт по ID
            product = Product.objects.get(id=product_id)
            # Формируем текст комментария
            initial_data['comment'] = f"Здравствуйте! Заинтересовал товар: {product.name} (ID: {product.id})."
        except Product.DoesNotExist:
            pass

    if request.method == 'POST':
        form = OrderForm(request.POST)
        if request.POST.get('imail') or request.POST.get('honeypot'):
            form.is_valid()
            send_telegram_notification(form.cleaned_data, True)
            messages.error(request, 'Система распосзнала, что вы бот!')
            return redirect('contacts')
        if form.is_valid():
            send_telegram_notification(form.cleaned_data)
            messages.success(request, 'Ваша заявка успешно отправлена!')
            return redirect('contacts') 
    else:
        # Передаем начальные данные в форму при GET-запросе
        form = OrderForm(initial=initial_data)

    context = {'form': form}
    return render(request, "contacts.html", context)





def projects_page(request):
    return render(request, "projects.html")
