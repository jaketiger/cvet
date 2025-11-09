# cart/context_processors.py

from .cart import Cart

def cart(request):
    """
    Этот контекстный процессор делает объект 'cart' доступным
    во всех шаблонах, которые рендерятся через RequestContext.
    """
    return {'cart': Cart(request)}