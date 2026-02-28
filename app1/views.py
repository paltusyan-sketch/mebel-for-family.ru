import requests
from django.http import HttpResponse
from django.conf import settings
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from .models import Product
from .forms import OrderForm
from random import choice

# Create your views here.

def send_telegram_notification(data, is_spam=False, chat_id=settings.SETTING_TELEGRAM_CHAT_ID):
    if data['comment']:
        comment = f"\nКомментарий: <b>{data['comment']}</b>"
    else:
        comment = ""
    
    if is_spam:
        spam_message = f"СПАМ !!!\n\n<b>imail:</b> {data['imail'] if data['imail'] else 'None'}\n<b>honeypot:</b> {data['honeypot'] if data['honeypot'] else 'None'}\n\n"
    else:
        spam_message = ""


    raw_phone = data['phone'].replace(' ', '').replace('(', '').replace(')', '').replace('-', '')
    message = spam_message + f"Имя: <b>{data['name']}</b>\nТелефон: <b>{raw_phone}</b>" + comment

    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    params = {
        'chat_id': chat_id,
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
            form.cleaned_data['imail'] = request.POST.get('imail')
            form.cleaned_data['honeypot'] = request.POST.get('honeypot')
            send_telegram_notification(form.cleaned_data, True, chat_id=settings.SETTING_TELEGRAM_CHAT_ID)
            messages.error(request, 'Система распосзнала, что вы бот!')
            return redirect('main')
        if form.is_valid():
            send_telegram_notification(form.cleaned_data, False, chat_id=settings.TELEGRAM_CHAT_ID)
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
  
    images = ([product.main_image.url] if product.main_image else []) + [*(i.image.url for i in product.images.all())]
   
    

    context = {'product' : product, "images" : images}
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
            form.cleaned_data['imail'] = request.POST.get('imail')
            form.cleaned_data['honeypot'] = request.POST.get('honeypot')
            send_telegram_notification(form.cleaned_data, True, chat_id=settings.SETTING_TELEGRAM_CHAT_ID)
            messages.error(request, 'Система распосзнала, что вы бот!')
            return redirect('contacts')
        if form.is_valid():
            send_telegram_notification(form.cleaned_data, False, chat_id=settings.TELEGRAM_CHAT_ID)
            messages.success(request, 'Ваша заявка успешно отправлена!')
            return redirect('contacts') # Перенаправляем на ту же страницу
    else:
        # Если метод GET, создаем пустую форму
        form = OrderForm()

    context = {'form': form}
    return render(request, "contacts.html", context)



def policy_page(request):
    products = Product.objects.all()
    # images = []
    # for i in products:
    #     images.append()
    context = {
        "products" : products,
    }
    return render(request, "policy.html", context)



def projects_page(request):
    return render(request, "projects.html")
