from numpy.random import seed
from sim import compile_results, run


seed(3)

basic_results, cs_results, opt_results = [], [], []

for i in range(1000):
    run(basic_results)

compile_results(results=basic_results, output='basic')

n = 20
for i in range(2, n+1):
    run(cs_results, capacity=i)

compile_results(results=cs_results, output='cs')

for i in range(1000):
    run(opt_results, capacity=4)

compile_results(results=opt_results, output='opt')
