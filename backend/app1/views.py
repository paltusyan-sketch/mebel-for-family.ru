import requests
import json
from django.http import HttpResponse, JsonResponse
from django.conf import settings
from django.contrib import messages
from django.db.models import Q
from django.shortcuts import render, get_object_or_404, redirect
from .models import Product, Category, Setting, FAQItem, RedirectLink
from .forms import OrderForm
from random import choice
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from .utils import send_telegram_msg
from user_agents import parse

# Create your views here.

def index_page(request):

    current_url = request.path
    all_potential_faqs = FAQItem.objects.filter(
        Q(page='main') | Q(url_path__isnull=False)
    ).distinct()

    faqs = [
        faq for faq in all_potential_faqs 
        if faq.page == 'main' or (faq.url_path and faq.url_path in current_url)
    ]

    context = {"form": OrderForm()}
    context["categories"] = Category.objects.filter(is_active=True)
    context["faqs"] = faqs
    return render(request, "index.html", context)


def catalog_page(request, category_slug=None):

    active_products = Product.objects.filter(is_active=True, category__is_active=True)

    if category_slug:
        products = active_products.filter(category__category_slug=category_slug)
    else:
        products = active_products

    paginator = Paginator(products, 6)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    context = {"products": page_obj}

    current_url = request.path
    all_potential_faqs = FAQItem.objects.filter(
        Q(page='catalog') | Q(url_path__isnull=False)
    ).distinct()
    faqs = [
        faq for faq in all_potential_faqs 
        if faq.page == 'catalog' or (faq.url_path and faq.url_path in current_url)
    ]
    context["faqs"] = faqs
    context["categories"] = Category.objects.filter(is_active=True)
    return render(request, "catalog.html", context)


def product_page(request, category_slug, product_slug):
    product = get_object_or_404(
        Product,
        product_slug=product_slug,
        category__category_slug=category_slug,  # Дополнительная проверка для безопасности
        is_active=True,
        category__is_active=True,
    )

    images = ([product.main_image.url] if product.main_image else []) + [
        *(i.image.url for i in product.images.all())
    ]
    images_webp = ([product.main_image_webp.url] if product.main_image_webp else []) + [
        *(i.image_webp.url for i in product.images.all())
    ]
    combined_images = list(zip(images, images_webp))
    
    product_url = request.path
    print(product_url)
    all_potential_faqs = FAQItem.objects.filter(
        Q(product=product) | Q(url_path__isnull=False)
    ).distinct()
    faqs = [
        faq for faq in all_potential_faqs 
        if faq.product == product or (faq.url_path and faq.url_path in product_url)
    ]
    print(faqs)

    context = {"product": product, "combined_images": combined_images}
    context["faqs"] = faqs
    return render(request, "product.html", context)


def contacts_page(request):
    initial_data = {}
    product_slug = request.GET.get("product_slug")  

    if product_slug:
        try:
            product = Product.objects.get(product_slug=product_slug)
            initial_data["comment"] = (
                f"Здравствуйте! Заинтересовал товар: {product.name}."
            )
        except Product.DoesNotExist:
            pass

    current_url = request.path

    all_potential_faqs = FAQItem.objects.filter(
        Q(page='contacts') | Q(url_path__isnull=False)
    ).distinct()

    faqs = [
        faq for faq in all_potential_faqs 
        if faq.page == 'contacts' or (faq.url_path and faq.url_path in current_url)
    ]

    context = {"form": OrderForm(initial=initial_data)}
    context["faqs"] = faqs
    context["seo_adress"] = (
        Setting.objects.first().address.replace("&nbsp;", " ").replace("<br>", " ")
    )  # временно
    return render(request, "contacts.html", context)


def policy_page(request):
    products = Product.objects.all()
        
    current_url = request.path
    all_potential_faqs = FAQItem.objects.filter(
        Q(page='policy') | Q(url_path__isnull=False)
    ).distinct()
    faqs = [
        faq for faq in all_potential_faqs 
        if faq.page == 'policy' or (faq.url_path and faq.url_path in current_url)
    ]
    context = {
        "products": products,
    }
    context["faqs"] = faqs
    return render(request, "policy.html", context)


def projects_page(request):

    current_url = request.path
    all_potential_faqs = FAQItem.objects.filter(
        Q(page='projects') | Q(url_path__isnull=False)
    ).distinct()
    faqs = [
        faq for faq in all_potential_faqs 
        if faq.page == 'projects' or (faq.url_path and faq.url_path in current_url)
    ]

    context = {}
    context["faqs"] = faqs
    return render(request, "projects.html", context)


def restoration_page(request):

    current_url = request.path
    all_potential_faqs = FAQItem.objects.filter(
        Q(page='restoration') | Q(url_path__isnull=False)
    ).distinct()
    faqs = [
        faq for faq in all_potential_faqs 
        if faq.page == 'restoration' or (faq.url_path and faq.url_path in current_url)
    ]
    print(faqs)

    context = {}
    context["faqs"] = faqs
    return render(request, "restoration.html", context)


def cooperation_page(request):

    current_url = request.path
    all_potential_faqs = FAQItem.objects.filter(
        Q(page='cooperation') | Q(url_path__isnull=False)
    ).distinct()
    faqs = [
        faq for faq in all_potential_faqs 
        if faq.page == 'cooperation' or (faq.url_path and faq.url_path in current_url)
    ]

    context = {}
    context["faqs"] = faqs
    return render(request, "cooperation.html", context)
 

def api_order_submit(request):
    # return JsonResponse({'status': 'error', 'errors': {'phone': ['Номер телефона заполнен криво!']}}, status=400)
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Метод не разрешен'}, status=405)
        
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Кривой JSON'}, status=400)

    form = OrderForm(data)
    
    if form.is_valid():
        clean = form.cleaned_data 

        is_spam = True if data.get("imail") or data.get("honeypot") else False
        chat_id = settings.SETTING_TELEGRAM_CHAT_ID if is_spam else settings.TELEGRAM_CHAT_ID

        raw_phone = (
            clean["phone"]
            .replace(" ", "")
            .replace("(", "")
            .replace(")", "")
            .replace("-", "")
        )

        if is_spam:
            spam_message = f"СПАМ !!!\n\n<b>imail:</b> {str(data.get('imail', 'None'))[:800]}\n<b>honeypot:</b> {str(data.get('honeypot', 'None'))[:800]}\n\n"
        else:
            spam_message = ""

        if clean.get("comment"):
            comment = f"\nКомментарий: <b>{clean['comment']}</b>"
        else:
            comment = ""

        message = (
            spam_message
            + f"Имя: <b>{clean['name']}</b>\nТелефон: <b>{raw_phone}</b>"
            + comment
        )
        
        send_telegram_msg(message=message, chat_id=chat_id, disable_notification=is_spam)
        return JsonResponse({'status': 'success', 'message': 'Ваша заявка успешно отправлена!'})

    return JsonResponse({
        'status': 'error', 
        'errors': form.errors.get_json_data()
    }, status=400)


def smart_redirect_view(request, short_code):
    link = get_object_or_404(RedirectLink, short_code=short_code, is_active=True)
    
    # Считаем клики для статистики
    link.clicks_count += 1
    link.save()

    ip_address = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', 'Unknown IP'))
    user_agent = request.META.get('HTTP_USER_AGENT', 'Unknown Device')
    user_agent_parsed = parse(request.META.get('HTTP_USER_AGENT', ''))

    if user_agent_parsed.is_mobile:
        device_type = "📱 Смартфон"
    elif user_agent_parsed.is_tablet:
        device_type = "📟 Планшет"
    else:
        device_type = "💻 Компьютер"

    browser_name = user_agent_parsed.browser.family

    try:
        # Стучимся к бесплатному мировому API (lang=ru вернет города на русском)
        geo_url = f"http://ip-api.com/json/{ip_address}?lang=ru"
        geo_res = requests.get(geo_url, timeout=3).json()
        
        # Если сервис успешно определил IP
        if geo_res.get('status') == 'success':
            country = geo_res.get('country', 'Неизвестно')
            city = geo_res.get('city', 'Неизвестно')
            geo_data = f"{country}, {city}"
        else:
            # Если прилетел локальный IP (127.0.0.1), сервис вернет fail
            geo_data = "🌍 Локалка / Гео не определено"
    except Exception as e:
        # Если вдруг в дата-центре отвалится интернет, сайт не упадет, а выдаст заглушку
        geo_data = f"🌍 Ошибка сети / Гео недоступно \n{e}"

    message = (
        f"<b>🎫 Визитка. Код:</b> <code>/r/{short_code}</code>\n"
        f"<b>📊 Переход номер:</b> <code>{link.clicks_count}</code>\n"
        f"<b>🌐 IP гостя:</b> <code>{ip_address}</code>\n"
        f"<b>📍 Геолокация:</b> <code>{geo_data}</code>\n"
        f"<b>🛠 Устройство:</b> <code>{device_type} ({browser_name})</code>\n"
        f"<b>↪️ Редирект:</b> <code>{link.target_url}</code>\n"
    )
    send_telegram_msg(message=message) if link.send_log else None
    return redirect(link.target_url)
