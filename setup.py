"""
打包成一个可执行模块。

该配置文件用于将 HAT 框架打包成 Python 库或可执行命令行工具。
"""
import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    # 关于项目的介绍 - 随便写都可以
    name="HuaceAutoTest",
    version="1.0.0",
    author="wyf",
    description="UI自动化测试工具",
    license="GPLv3",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://www.hctestedu.com",
    project_urls={
        "Bug Tracker": "https://www.hctestedu.com",
        "Contact Us": "https://www.hctestedu.com",
    },

    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Operating System :: OS Independent",
    ],
    # 需要安装的依赖 -- 工具依赖
    install_requires=[
        "pytest>=7.1.3",
        "Jinja2>=3.1.6",
        "pandas>=1.5.3",
        "PyMySQL>=1.1.2",
        "allure-pytest>=2.13.5",
        "playwright>=1.45.0",
        "urllib3>=1.26.20",
        "PyYAML>=6.0.3",
        "pyyaml-include>=1.3.1",
        "numpy>=1.24.0",
        "tqdm>=4.67.0",
        "loguru>=0.7.3",
        "openpyxl>=3.1.5",
        "ddddocr",
        "Pillow>=11.0.0",
        "beautifulsoup4>=4.14.0",
    ],
    packages=setuptools.find_packages(),
    python_requires=">=3.8",
    # 生成一个 可执行文件 例如 windows下面 .exe
    entry_points={
        'console_scripts': [
            # 可执行文件的名称=执行的具体代码方法
            'huace-test=main:run'
        ]
    },
    zip_safe=False
)