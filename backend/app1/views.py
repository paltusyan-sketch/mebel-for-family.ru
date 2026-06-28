import requests
import json
from django.http import HttpResponse, JsonResponse
from django.conf import settings
from django.contrib import messages
from django.db.models import Q
from django.shortcuts import render, get_object_or_404, redirect
from .models import Product, Category, Setting, FAQItem
from .forms import OrderForm
from random import choice
from django.views.decorators.csrf import csrf_exempt

# Create your views here.


def send_telegram_notification(
    data, is_spam=False, chat_id=settings.SETTING_TELEGRAM_CHAT_ID
):
    if data["comment"]:
        comment = f"\nКомментарий: <b>{data['comment']}</b>"
    else:
        comment = ""

    if is_spam:
        spam_message = f"СПАМ !!!\n\n<b>imail:</b> {data['imail'] if data['imail'] else 'None'}\n<b>honeypot:</b> {data['honeypot'] if data['honeypot'] else 'None'}\n\n"
    else:
        spam_message = ""

    raw_phone = (
        data["phone"]
        .replace(" ", "")
        .replace("(", "")
        .replace(")", "")
        .replace("-", "")
    )
    message = (
        spam_message
        + f"Имя: <b>{data['name']}</b>\nТелефон: <b>{raw_phone}</b>"
        + comment
    )

    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    params = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML",
        "disable_notification": is_spam,
    }
    response = requests.post(url, data=params)


def index_page(request):
    # Если данные отправлены методом POST
    if request.method == "POST":
        form = OrderForm(request.POST)
        if request.POST.get("imail") or request.POST.get("honeypot"):
            form.is_valid()
            form.cleaned_data["imail"] = request.POST.get("imail")
            form.cleaned_data["honeypot"] = request.POST.get("honeypot")
            send_telegram_notification(
                form.cleaned_data, True, chat_id=settings.SETTING_TELEGRAM_CHAT_ID
            )
            messages.error(request, "Система распознала, что вы бот!")
            return redirect(request.path)
        if form.is_valid():
            send_telegram_notification(
                form.cleaned_data, False, chat_id=settings.TELEGRAM_CHAT_ID
            )
            messages.success(request, "Ваша заявка успешно отправлена!")
            return redirect("main")  # Перенаправляем на ту же страницу
    else:
        # Если метод GET, создаем пустую форму
        form = OrderForm()

    current_url = request.path  # вернет "/"
    # Забираем потенциальные вопросы для главной
    all_potential_faqs = FAQItem.objects.filter(
        Q(page='main') | Q(url_path__isnull=False)
    ).distinct()
    # Фильтруем: оставляем если в choices выбрана главная ИЛИ если url_path совпал с корнем
    faqs = [
        faq for faq in all_potential_faqs 
        if faq.page == 'main' or (faq.url_path and faq.url_path in current_url)
    ]

    context = {"form": form}
    context["categories"] = Category.objects.all()
    context["faqs"] = faqs
    print(faqs) if faqs else print(None)
    return render(request, "index.html", context)


def catalog_page(request, category_slug=None):

    if category_slug:
        products = Product.objects.filter(category__category_slug=category_slug)
        context = {"products": products}
    else:
        all_products = Product.objects.all()
        context = {"products": all_products}


    current_url = request.path  # вернет "/"
    # Забираем потенциальные вопросы для главной
    all_potential_faqs = FAQItem.objects.filter(
        Q(page='catalog') | Q(url_path__isnull=False)
    ).distinct()
    # Фильтруем: оставляем если в choices выбрана главная ИЛИ если url_path совпал с корнем
    faqs = [
        faq for faq in all_potential_faqs 
        if faq.page == 'catalog' or (faq.url_path and faq.url_path in current_url)
    ]
    context["faqs"] = faqs
    context["categories"] = Category.objects.all()
    return render(request, "catalog.html", context)


def product_page(request, category_slug, product_slug):
    product = get_object_or_404(
        Product,
        product_slug=product_slug,
        category__category_slug=category_slug,  # Дополнительная проверка для безопасности
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
        
    current_url = request.path  # вернет "/"
    # Забираем потенциальные вопросы для главной
    all_potential_faqs = FAQItem.objects.filter(
        Q(page='policy') | Q(url_path__isnull=False)
    ).distinct()
    # Фильтруем: оставляем если в choices выбрана главная ИЛИ если url_path совпал с корнем
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

    current_url = request.path  # вернет "/"
    # Забираем потенциальные вопросы для главной
    all_potential_faqs = FAQItem.objects.filter(
        Q(page='projects') | Q(url_path__isnull=False)
    ).distinct()
    # Фильтруем: оставляем если в choices выбрана главная ИЛИ если url_path совпал с корнем
    faqs = [
        faq for faq in all_potential_faqs 
        if faq.page == 'projects' or (faq.url_path and faq.url_path in current_url)
    ]

    context = {}
    context["faqs"] = faqs
    return render(request, "projects.html", context)


def restoration_page(request):

    current_url = request.path  # вернет "/"
    # Забираем потенциальные вопросы для главной
    all_potential_faqs = FAQItem.objects.filter(
        Q(page='restoration') | Q(url_path__isnull=False)
    ).distinct()
    # Фильтруем: оставляем если в choices выбрана главная ИЛИ если url_path совпал с корнем
    faqs = [
        faq for faq in all_potential_faqs 
        if faq.page == 'restoration' or (faq.url_path and faq.url_path in current_url)
    ]
    print(faqs)

    context = {}
    context["faqs"] = faqs
    return render(request, "restoration.html", context)


def cooperation_page(request):

    current_url = request.path  # вернет "/"
    # Забираем потенциальные вопросы для главной
    all_potential_faqs = FAQItem.objects.filter(
        Q(page='cooperation') | Q(url_path__isnull=False)
    ).distinct()
    # Фильтруем: оставляем если в choices выбрана главная ИЛИ если url_path совпал с корнем
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

    if data.get("imail") or data.get("honeypot"):
        send_telegram_notification(data, is_spam=True, chat_id=settings.SETTING_TELEGRAM_CHAT_ID)
        return JsonResponse({'status': 'success', 'message': 'Заявка обрабатывается'})

    form = OrderForm(data)
    
    if form.is_valid():
        send_telegram_notification(form.cleaned_data, is_spam=False, chat_id=settings.TELEGRAM_CHAT_ID)
        return JsonResponse({'status': 'success', 'message': 'Ваша заявка успешно отправлена!'})

    return JsonResponse({
        'status': 'error', 
        'errors': form.errors.get_json_data()
    }, status=400)
