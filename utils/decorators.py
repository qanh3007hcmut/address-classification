from functools import wraps
import sys
import time

DEBUG = True
LEFT = 30

def track_input(var_name: str):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Lấy giá trị biến đầu vào từ args hoặc kwargs
            input_val = kwargs.get(var_name)
            if input_val is None:
                # Nếu không có trong kwargs, thử lấy theo vị trí (nếu tên var_name là đối số đầu)
                func_params = func.__code__.co_varnames
                if var_name in func_params:
                    idx = func_params.index(var_name)
                    if idx < len(args):
                        input_val = args[idx]

            print(f"{func.__name__}", " "*(LEFT - len(func.__name__)), f"|{input_val}|", end=" ")

            # Gọi hàm thật
            result = func(*args, **kwargs)

            print(f"-> |{result}|")

            return result
        return wrapper
    return decorator

def track_variable(var_name: str):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            def tracer(frame, event, arg):
                if event == "line" and frame.f_code == func.__code__:
                    local_vars = frame.f_locals
                    if var_name in local_vars:
                        val = local_vars[var_name]
                        print(f"{func.__name__}: {val}")
                return tracer

            sys.settrace(tracer)
            try:
                result = func(*args, **kwargs)
            finally:
                sys.settrace(None)

            print(f"{func.__name__}_return: {var_name} ({result})")
            return result
        return wrapper
    return decorator

def track_time_ns(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not DEBUG:
            return func(*args, **kwargs)
        
        start = time.time_ns()
        result = func(*args, **kwargs)
        end = time.time_ns()
        elapsed = end - start

        print(f"{func.__name__} executed in {elapsed / 1e6:.3f} ms ~ {elapsed / 1e9:.6f} s", "\n")
        return result
    return wrapper