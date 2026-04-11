# 华测教育 - 混合型企业级自动化测试框架工具
> APP 接口 WEB AI 多用途测试 
> 运行环境建议python3.8及以上（如果需要win7运行则不能高于3.8

> 如果想使用 AI ，请配置大模型相关接口环境变量
> 兼容openai接口的key：HAT_LLM_API_KEY
> (如果是ollama本地部署则随便填一个key即可)
> 兼容openai接口的地址：HAT_LLM_BASE_URL
> 大模型名称：HAT_LLM_MODEL_NAME

## 开发工具中运行 main.py

## 命令行使用 
### 安装到  Python 环境
python setup.py install
### python 环境中运行 hat运行

## 单独发布可执行程序
### 加密编译发布
pyarmor gen -O dist --expire "2026-07-31" --recursive --pack "hat_cli.spec" ./HAT main.py
dist文件夹下会有一个可执行文件

### 使用方式和上述一致