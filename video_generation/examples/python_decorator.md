# Python 装饰器

## 学习目标
- 理解装饰器的本质：高阶函数
- 掌握 @decorator 语法糖
- 学会编写带参数的装饰器
- 了解 functools.wraps 的作用

## 内容大纲

### 1. 什么是装饰器
装饰器是 Python 中的一种设计模式，本质上是一个函数，它接收一个函数作为参数，返回一个新的增强函数。

### 2. 基本语法
```python
def my_decorator(func):
    def wrapper(*args, **kwargs):
        print("调用前")
        result = func(*args, **kwargs)
        print("调用后")
        return result
    return wrapper

@my_decorator
def say_hello(name):
    print(f"Hello, {name}!")
```

### 3. 实用装饰器示例
- 计时器装饰器
- 日志装饰器
- 缓存装饰器

### 4. 带参数的装饰器
```python
def repeat(n):
    def decorator(func):
        def wrapper(*args, **kwargs):
            for _ in range(n):
                result = func(*args, **kwargs)
            return result
        return wrapper
    return decorator

@repeat(3)
def greet():
    print("Hello!")
```

### 5. functools.wraps
保留被装饰函数的元信息（__name__, __doc__）。
