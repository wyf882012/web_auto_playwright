import setuptools
"""
打包成一个 可执行模块
"""
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    # 关于项目的介绍 - 随便写都可以
    name="HuaceAutoTest",
    version="1.0.0",
    author="hctestedu.com",
    author_email="zhangfeng0103@live.com",
    description="华测教育-多端融合自动化测试工具",
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
        "pytest==7.1.3",  # 改为 7.1.3
        "Jinja2==3.1.6",  # 改为 3.1.6
        "pandas==1.5.3",
        "PyMySQL==1.1.2",  # 改为 1.1.2
        "allure-pytest==2.13.5",
        "selenium==4.2.0",  # 改为 4.2.0
        "urllib3==1.26.20",  # 改为 1.26.20
        "PyYAML==6.0.3",  # 改为 6.0.3
        "pyyaml-include==1.3.1",
        "numpy==1.24.0",
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