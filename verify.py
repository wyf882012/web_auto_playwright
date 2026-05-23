"""
Self-verification suite for HAT framework rewrite.
Run: python verify.py
"""
import sys
import os
import subprocess

os.chdir(os.path.dirname(os.path.abspath(__file__)))

passed = 0
failed = 0
errors = []

def check(name, condition, detail=''):
    global passed, failed
    if condition:
        passed += 1
        print(f'  [PASS] {name}')
    else:
        failed += 1
        msg = f'  [FAIL] {name} — {detail}'
        print(msg)
        errors.append(msg)

# ═══════════════════════════════════════════════════════════════
print('=== 1. Core Imports ===')
try:
    from HAT.config import cfg; check('HAT.config', True)
    from HAT.template import render; check('HAT.template', True)
    from HAT.locator import LocatorBuilder; check('HAT.locator', True)
    from HAT.parser import parse, load_context; check('HAT.parser', True)
    from HAT.plugin import CasesPlugin; check('HAT.plugin', True)
    from HAT.keywords import Keywords; check('HAT.keywords', True)
    from HAT.browser import BrowserManager; check('HAT.browser', True)
    from HAT.runner import TestRunner; check('HAT.runner', True)
    from HAT.pages.base import BasePage; check('pages.base', True)
    from HAT.pages.login import LoginPage; check('pages.login', True)
    from HAT.utils.step_logger import allure_step_with_log; check('utils.step_logger', True)
    from HAT.utils.script import exec_script; check('utils.script', True)
except Exception as e:
    check('ALL_IMPORTS', False, str(e))

# ═══════════════════════════════════════════════════════════════
print('\n=== 2. Config Singleton ===')
cfg2 = type(cfg)()
cfg.set('_verify_test', 42)
check('Config.get', cfg.get('_verify_test') == 42)
check('Config singleton (same store)', cfg2.get('_verify_test') == 42)
cfg.update({'a': 1, 'b': 2})
check('Config.update', cfg.get('a') == 1 and cfg.get('b') == 2)
check('Config.all returns dict', isinstance(cfg.all(), dict))
cfg.set('_verify_test', None)

# ═══════════════════════════════════════════════════════════════
print('\n=== 3. Template Renderer ===')
check('Simple var', render('hello {{name}}', {'name': 'world'}) == 'hello world')
check('Multiple vars', render('{{a}}+{{b}}={{c}}', {'a':'1','b':'2','c':'3'}) == '1+2=3')
check('None input', render(None, {}) is None)
check('No template', render('plain text', {}) == 'plain text')
check('Numeric value', render('{{n}}', {'n': 42}) == '42')

# ═══════════════════════════════════════════════════════════════
print('\n=== 4. Parser — Excel ===')
result = parse('examples/reelmate-cases-excel')
check('Has case_infos', 'case_infos' in result)
check('Has case_names', 'case_names' in result)
check('20 test cases', len(result['case_infos']) == 20,
      f'got {len(result["case_infos"])}')
check('All have base config', all('基础配置' in c for c in result['case_infos']))
check('All have steps', all('用例步骤' in c for c in result['case_infos']))
check('First case title', result['case_names'][0] == '登录页面元素完整性验证')
# DDT expansion
ddt_cases = [n for n in result['case_names'] if 'DSW' in n]
check('3 DDT expanded cases', len(ddt_cases) == 3, f'got {len(ddt_cases)}')
has_ddt = any('local_context' in c for c in result['case_infos']
              if 'DSW' in str(c.get('基础配置',{}).get('用例标题','')))
check('DDT case has local_context', has_ddt)

# Check context loading
cfg2 = type(cfg)()
check('Context base_url loaded', cfg2.get('base_url') is not None,
      f'base_url={cfg2.get("base_url")}')
check('Context _elements loaded', len(cfg2.get('_elements') or {}) >= 1,
      f'got {len(cfg2.get("_elements") or {})}')

# ═══════════════════════════════════════════════════════════════
print('\n=== 5. Parser — YAML ===')
if os.path.isdir('examples/reelmate-cases'):
    result_yaml = parse('examples/reelmate-cases')
    check('YAML parser works', len(result_yaml['case_infos']) > 0,
          f'got {len(result_yaml["case_infos"])} cases')
else:
    print('  [SKIP] reelmate-cases dir not found')

# ═══════════════════════════════════════════════════════════════
print('\n=== 6. Plugin ===')
plugin = CasesPlugin()
check('Has pytest_addoption', hasattr(plugin, 'pytest_addoption'))
check('Has pytest_generate_tests', hasattr(plugin, 'pytest_generate_tests'))
check('Has pytest_collection_modifyitems', hasattr(plugin, 'pytest_collection_modifyitems'))

# ═══════════════════════════════════════════════════════════════
print('\n=== 7. Locator Builder (class structure) ===')
check('Has from_yaml', hasattr(LocatorBuilder, 'from_yaml'))
check('Has from_dict', hasattr(LocatorBuilder, 'from_dict'))
check('Has from_legacy', hasattr(LocatorBuilder, 'from_legacy'))
check('Has _BUILDERS map', hasattr(LocatorBuilder, '_BUILDERS'))
valid_types = {'role','label','placeholder','text','alt','testid','css','xpath'}
check('All 8 locator types supported',
      set(LocatorBuilder._BUILDERS.keys()) == valid_types)

# Verify YAML file
import yaml
with open('HAT/locators/login_page.yaml', encoding='utf-8') as f:
    loc_data = yaml.safe_load(f)
check('login_page.yaml valid', isinstance(loc_data, dict) and len(loc_data) == 8,
      f'{len(loc_data)} elements')
check('All YAML types valid',
      all(v.get('type') in LocatorBuilder._BUILDERS for v in loc_data.values()))

# ═══════════════════════════════════════════════════════════════
print('\n=== 8. Browser Manager (class structure) ===')
check('Has start', hasattr(BrowserManager, 'start'))
check('Has stop', hasattr(BrowserManager, 'stop'))
check('Has _launch', hasattr(BrowserManager, '_launch'))
check('Has _setup_locators', hasattr(BrowserManager, '_setup_locators'))

# ═══════════════════════════════════════════════════════════════
print('\n=== 9. Keywords — All 45+ Methods ===')
cn_methods = [
    '访问网址', '页面刷新', '页面前进', '页面后退',
    '点击元素', '输入内容', '输入内容追加', '清空输入框',
    '鼠标悬停', '双击元素', '右键点击', '滚动到元素',
    '选择下拉框选项', '选择下拉框选项按值', '勾选复选框', '取消勾选', '上传文件',
    '获取元素文本', '获取元素属性', '获取当前URL', '获取页面标题',
    '断言文本', '断言文本相等', '断言文本包含', '断言文本不相等',
    '断言数字相等', '断言数字不相等', '断言数字大于', '断言数字小于',
    '断言数字大于等于', '断言数字小于等于',
    '断言浏览器路径', '断言元素存在', '断言元素不存在', '断言页面标题',
    'iframe_switch_to', 'iframe_to_default_content',
    'switch_to_latest_handle', 'switch_to_appoint_handle', '关闭当前页面',
    '强制等待', '窗口最大化', '关闭浏览器',
    '键盘按键', '拖拽元素', '滚动页面', '执行JS',
    '接受弹窗', '取消弹窗', '获取弹窗文本',
    'store_text', 'random_six_digit_number',
    '提取数据MYSQL', 'image_recognition',
    'AI操作', 'AI断言', 'ex_invoke',
]
missing = [m for m in cn_methods if not hasattr(Keywords, m)]
check(f'{len(cn_methods)} Chinese keywords present',
      len(missing) == 0, f'missing: {missing}')
check('Has _locator helper', hasattr(Keywords, '_locator'))
check('Has screenshot method', hasattr(Keywords, 'screenshot'))
check('Has _ai_vision method', hasattr(Keywords, '_ai_vision'))

# ═══════════════════════════════════════════════════════════════
print('\n=== 10. POM Pages ===')
base_methods = ['click', 'fill', 'check', 'get_text', 'is_visible',
                'assert_visible', 'open', 'get_url', 'assert_url_contains',
                'get_title', 'wait']
for m in base_methods:
    check(f'BasePage.{m}', hasattr(BasePage, m))

lp_methods = ['navigate_to_login', 'login', 'enter_username', 'enter_password',
              'clear_username', 'clear_password', 'click_login_button',
              'agree_to_terms', 'is_on_login_page', 'is_logged_in',
              'get_error_message', 'verify_login_page_elements',
              'verify_login_success', 'verify_login_failed']
for m in lp_methods:
    check(f'LoginPage.{m}', hasattr(LoginPage, m))

# ═══════════════════════════════════════════════════════════════
print('\n=== 11. Script Executor ===')
ctx = {'x': 0}
exec_script('context["x"] = 99', ctx)
check('exec_script runs Python', ctx['x'] == 99)
exec_script('', {}); check('exec_script empty str', True)
exec_script(None, {}); check('exec_script None', True)
# Multi-line script
exec_script('context["a"] = 1\ncontext["b"] = 2', ctx)
check('exec_script multi-line', ctx.get('a') == 1 and ctx.get('b') == 2)

# ═══════════════════════════════════════════════════════════════
print('\n=== 12. No Stale Module References ===')
# Check that no .py files reference removed modules
stale_patterns = [
    'g_context', 'globalContext', 'WebCaseContext',
    'web_keywords', 'YamlCaseParser', 'ExcelCaseParser',
    'login_page_locator.py', 'VarRender', 'allure_step_logger',
    'run_script.exec_script', 'load_excel_files', 'load_yaml_files',
    'from HAT.core', 'from HAT.context', 'from HAT.parse.', 'from HAT.ddt',
]
found_stale = []
for root, dirs, files in os.walk('HAT'):
    dirs[:] = [d for d in dirs if d not in ('__pycache__', 'extend')]
    for fn in files:
        if not fn.endswith('.py'):
            continue
        fpath = os.path.join(root, fn)
        with open(fpath, encoding='utf-8') as f:
            content = f.read()
        for pat in stale_patterns:
            if pat in content:
                # Allow CasesPlugin reference (still used as class name)
                if pat == 'CasesPlugin' and 'class CasesPlugin' in content:
                    continue
                found_stale.append(f'{fpath}: {pat}')
check('No stale module references',
      len(found_stale) == 0, f'Found: {found_stale[:10]}')

# ═══════════════════════════════════════════════════════════════
print('\n=== 13. Pytest Collection ===')
pytest_result = subprocess.run(
    [sys.executable, '-m', 'pytest', '--collect-only',
     '--type=excel', '--cases=examples/reelmate-cases-excel', '-q', '--no-header'],
    capture_output=True, text=True, timeout=30,
)
check('pytest exits cleanly', pytest_result.returncode in (0, 5),
      f'rc={pytest_result.returncode}')
check('20 tests collected', '20 tests collected' in pytest_result.stdout.replace('\n',' '),
      f'output: {pytest_result.stdout.split(chr(10))[0]}')
# Check for parametrized DDT cases
check('DDT cases in collection', 'DSW-1001' in pytest_result.stdout)

# ═══════════════════════════════════════════════════════════════
print('\n=== 14. CLI Help ===')
help_result = subprocess.run(
    [sys.executable, 'main.py', '--help'],
    capture_output=True, text=True, timeout=10,
)
check('--help works', help_result.returncode == 0)
check('--headless in help', '--headless' in help_result.stdout)
check('--browser in help', '--browser' in help_result.stdout)
check('--workers in help', '--workers' in help_result.stdout)
check('--version in help', '--version' in help_result.stdout)

# ═══════════════════════════════════════════════════════════════
print(f'\n{"="*60}')
print(f'  RESULTS: {passed} passed, {failed} failed, '
      f'{passed+failed} total checks')
print(f'{"="*60}')
if errors:
    for e in errors:
        print(f'  {e}')
sys.exit(0 if failed == 0 else 1)
