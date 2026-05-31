

from django import template

register = template.Library()

@register.filter(name='format_price')
def format_price(price):
    try:
        price = str(price)                                                      # Приводим в удобный вид.
        price = price.replace(" ","")
        price = price.replace(",","")
        price = price.replace(".","")
        price = price.replace("₽","")

        if len(price) > 3:
            number_of_commas = len(price) // 3                                  # Определяем количество запятых.  
            if len(price) % 3 == 0:
                number_of_commas -= 1

            positions_of_commas = [-4]
            while len(positions_of_commas) < number_of_commas:                  # Определяем позиции запятых.
                positions_of_commas += [positions_of_commas[-1] - 4]
                # print(positions_of_commas)

            while len(positions_of_commas) != 0:                                # Ставим запятые на нужные позиции.
                price = price[0:positions_of_commas[0]+1] + " " + price[positions_of_commas[0]+1:]
                del positions_of_commas[0]
        # print("₽" + price)
        return price
    except:
        return price