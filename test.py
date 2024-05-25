from timeit import timeit

size = 100
test_dict = {i: i for i in range(size)}

time1 = timeit("[test_dict[i] for i in range(size)]", globals=globals())
time2 = timeit("[test_dict.get(i) for i in range(size)]", globals=globals())

print("[...] method:", time1)
print(".get(...) method:", time2)
