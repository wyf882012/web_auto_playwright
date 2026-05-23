"""
Jinja2 variable renderer — replaces {{variable}} placeholders in test data.
"""

from jinja2 import Template


def render(target, context: dict):
    """Render Jinja2 templates in *target* using *context* dict values.

    >>> render("{{greeting}}, {{name}}", {"greeting": "Hello", "name": "World"})
    'Hello, World'
    """
    if target is None:
        return None
    return Template(str(target)).render(context)
