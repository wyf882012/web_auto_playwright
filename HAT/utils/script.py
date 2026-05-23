"""
Pre / post script executor — runs user-supplied Python code strings.

Used in test cases via:
  前置脚本:
    - context.update({'key': 'value'})
  后置脚本:
    - context.update({'cleanup': True})
"""


def exec_script(code: str, context: dict):
    """Execute *code* string in a namespace containing *context* dict."""
    if not code:
        return
    exec(code, {"context": context})
