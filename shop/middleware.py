# shop/middleware.py

from django.utils.deprecation import MiddlewareMixin


class AdminViewportMiddleware(MiddlewareMixin):
    """
    Промежуточное ПО, которое добавляет мета-тег viewport
    на все страницы админ-панели.
    """

    def process_response(self, request, response):
        # Проверяем, что это страница админки и что это HTML-ответ
        if request.path.startswith('/admin/') and 'text/html' in response.get('Content-Type', ''):
            # Конвертируем контент в строку для поиска и замены
            content = response.content.decode(response.charset)

            # Строка, которую мы хотим вставить
            viewport_tag = '<meta name="viewport" content="width=device-width, initial-scale=1.0">'

            # Вставляем наш тег сразу после открывающего тега <head>
            # (используем case-insensitive замену на всякий случай)
            import re
            content = re.sub(r'<head>', f'<head>\n    {viewport_tag}', content, count=1, flags=re.IGNORECASE)

            # Обновляем контент ответа
            response.content = content.encode(response.charset)

            # Обновляем заголовок Content-Length, так как мы изменили размер контента
            if 'Content-Length' in response:
                response['Content-Length'] = len(response.content)

        return response