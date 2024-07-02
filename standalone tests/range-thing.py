import random
import time


n = random.random()
rl = 0
rh = 1
r = range(rl, rh)
steps = .2

print(n, r, steps)


def clamp(minimum, x, maximum):
    return max(minimum, min(x, maximum))


def clamp_number_to_range_steps(n, start, end, step) -> float:
    n = clamp(start, n, end)
    return round(n / step) * step


t1 = time.perf_counter()
res = round(round(n / steps) * steps, 2)
end = time.perf_counter() - t1
print(res, end)
t1 = time.perf_counter()
res = clamp_number_to_range_steps(n, 0, 1, 0.2)
end = time.perf_counter() - t1
print(res, end)
