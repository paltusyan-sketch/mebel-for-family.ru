from django import forms


class OrderForm(forms.Form):
    name = forms.CharField(label='Ваше имя', max_length=100, widget=forms.TextInput(attrs={'placeholder': 'Имя'}))
    phone = forms.CharField(label='Номер телефона', max_length=20, widget=forms.TextInput(attrs={'class': 'form-input phone-mask', 'placeholder': '+7 (999) 123-45-67'}))
    comment = forms.CharField(
        label="Комментарий/Вопрос",
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "form-input",
                "rows": 5,
                "placeholder": "Например: Нужен замер кухни или расчет шкафа-купе...",
            }
        ),
    )
