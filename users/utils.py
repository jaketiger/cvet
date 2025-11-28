# users/utils.py
import re


def normalize_phone(phone):
    """
    Приводит номер к формату 79991112233.
    Если номер невалидный, возвращает None.
    """
    if not phone:
        return None

    # Оставляем только цифры
    digits = re.sub(r'\D', '', phone)

    # Проверка длины и первой цифры для РФ (11 цифр, начинается с 7 или 8)
    if len(digits) == 11:
        if digits.startswith('8'):
            return '7' + digits[1:]  # Меняем 8 на 7
        elif digits.startswith('7'):
            return digits

    # Если вдруг номер 10 цифр (забыли +7), добавляем 7
    elif len(digits) == 10:
        return '7' + digits

    # Если формат совсем не тот, возвращаем как есть (пусть валидатор формы ругается)
    # или None, если хотим строгую проверку.
    return digits