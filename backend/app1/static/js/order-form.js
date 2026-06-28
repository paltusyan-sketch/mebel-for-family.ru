

document.addEventListener('DOMContentLoaded', () => {
    const phoneInput = document.getElementById('id_phone');
    if (phoneInput) {
        phoneInput.addEventListener('input', (e) => {
            let value = e.target.value.replace(/\D/g, '');
            if (!value) { e.target.value = ''; return; }
            if (value[0] === '8') value = '7' + value.slice(1);
            if (value[0] !== '7') value = '7' + value;
            if (value.length > 11) value = value.slice(0, 11);

            let formattedValue = '+7';
            if (value.length > 1) formattedValue += ' (' + value.slice(1, 4);
            if (value.length >= 5) formattedValue += ') ' + value.slice(4, 7);
            if (value.length >= 8) formattedValue += '-' + value.slice(7, 9);
            if (value.length >= 10) formattedValue += '-' + value.slice(9, 11);
            e.target.value = formattedValue;
        });

        phoneInput.addEventListener('keydown', (e) => {
            if (e.key === 'Backspace' && e.target.value.replace(/\D/g, '').length <= 1) {
                e.target.value = '';
            }
        });
    }
});



document.addEventListener('DOMContentLoaded', () => {
    const form = document.querySelector('form');
    if (!form) return;

    form.onsubmit = async function(e) {
        e.preventDefault(); // 1. ЖЕСТКО ТОРМОЗИМ ПЕРЕЗАГРУЗКУ СТРАНИЦЫ!

        // 2. Проверяем галочку согласия персональных данных
        if (!document.getElementById('gdpr_check').checked) {
            alert('Поставь галку, иначе мебель не приедет!');
            return;
        }

        // 3. Собираем данные из абсолютно всех полей, включая ловушки спама
        const formData = {
            name: document.getElementById('id_name').value,
            phone: document.getElementById('id_phone').value,
            comment: document.getElementById('id_comment').value,
            imail: document.getElementById('id_email').value, // Наша ловушка
            honeypot: document.querySelector('input[name="honeypot"]').value // Наша ловушка
        };

        // 4. Вытаскиваем встроенный CSRF-токен Джанго для защиты запроса
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

        try {
            // 5. Отправляем текстовую СМС-ку (JSON) на наш новый эндпоинт
            const response = await fetch('/api/v1/order-submit/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify(formData)
            });

            const data = await response.json();
            const msgBlock = document.getElementById('api-message');

            // СКЛЕИВАЕМ ПАЛЫЦЫ ИДЕАЛЬНО: Разбираем все сценарии от Джанго
            if (data.status === 'success') {
                // Сценарий 1: Полный успех
                msgBlock.innerText = data.message;
                msgBlock.classList.remove('hidden');
                msgBlock.classList.add('bg-emerald-100', 'text-emerald-800', 'my-fade-in');
                form.reset();
                const commentInput = document.getElementById('id_comment');
                if (commentInput) {
                    commentInput.value = ''; 
                }
            } 
            else if (data.errors) {
                // Сценарий 2: Сервер прислал конкретный словарь ошибок формы
                msgBlock.innerText = "Ошибка заполнения. Проверьте поля формы, бро!";
                msgBlock.classList.remove('hidden');
                msgBlock.classList.add('bg-rose-100', 'text-rose-800', 'my-fade-in');
                console.log("Ошибки полей:", data.errors);
                
                // Здесь в будущем мы сможем запустить цикл и подрисовать ошибки под инпутами
            } 
            else if (data.message) {
                // Сценарий 3: Сервер прислал просто текстовую ошибку (Кривой JSON, не POST и т.д.)
                console.error("Техническая ошибка сервера:", data.message);
                msgBlock.innerText = data.message;
                msgBlock.classList.remove('hidden');
                msgBlock.classList.add('bg-rose-100', 'text-rose-800', 'my-fade-in');
            } 
            else {
                // Сценарий 4: На всякий пожарный, если прилетела вообще неведомая херня
                alert("Произошла неизвестная ошибка на сервере.");
            }

        } catch (err) {
            console.error("Бля, связь с сервером оборвалась:", err);
            alert("Ошибка отправки. Попробуйте позже.");
        }
    };
});
