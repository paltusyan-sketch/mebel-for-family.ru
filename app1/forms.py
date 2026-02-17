from django import forms



class OrderForm(forms.Form):
    name = forms.CharField(label='Ваше имя', max_length=100)
    phone = forms.CharField(label='Номер телефона', max_length=20)
    comment = forms.CharField(label='Комментарий/Вопрос', widget=forms.Textarea, required=False)