import os

print(os.getenv('HAT_LOG_LEVEL', "INFO"))
print(os.path.join(os.getcwd()))