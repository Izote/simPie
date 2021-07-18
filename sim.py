from __future__ import annotations
from typing import Any, Dict, Generator, List, Union, TYPE_CHECKING
from numpy.random import poisson, uniform
from pandas import DataFrame
from simpy import Environment, Resource


if TYPE_CHECKING:
    from simpy import Event, Environment


class Kitchen:
    def __init__(self, sys: Dict) -> None:
        self._sys = sys
        self._oven_time = None

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}' \
               f'(bake_time={self._oven_time})'

    def bake(
            self,
            env: Environment,
            pizza: Pizza
    ) -> Generator[Event, Any, Any]:

        start = env.now
        print(f'Pizza #{pizza.order} starts baking at {start}')

        yield env.timeout(self._oven_time)
        end = env.now
        pizza.set_finish_time(time=end)

        self._sys['DATA'].append(pizza)
        print(f'Pizza #{pizza.order} leaves the oven and '
              f'is packed for delivery at {end}.')

    def set_oven_time(self, minutes: Union[float, int]) -> None:
        self._oven_time = minutes


class Pizza:
    def __init__(
            self,
            order: int,
            order_time: int,
            recipe: Dict[str, float],
            costs: Dict[str, float]
    ) -> None:
        self._recipe = recipe
        self._cost = self._get_cost(costs)
        self._price = 8.00
        self._order = order
        self._order_time = order_time
        self._finish_time = None

        print(f'Pizza #{self._order} is ordered at {self._order_time}...')

    def __repr__(self):
        return f'{self.__class__.__name__}' \
               f'(order={self._order}, ' \
               f'order_time={self._order_time}, ' \
               f'finish_time={self._finish_time},' \
               f'cost={self._cost},' \
               f'price={self._price}'

    @property
    def order(self) -> int:
        return self._order

    @property
    def order_time(self) -> int:
        return self._order_time

    @property
    def recipe(self) -> Dict[str, float]:
        return self._recipe

    @property
    def finish_time(self) -> int:
        return self._finish_time

    def _get_cost(self, costs: Dict[str, float]) -> float:
        ingredients = list(costs.keys())

        sub_costs = [self._recipe[ing] * costs[ing] for ing in ingredients]
        total_cost = round(sum(sub_costs), 2)

        return total_cost

    def set_finish_time(self, time: float):
        self._finish_time = time

    def get_data(self) -> Dict:
        return {
            'order': self._order,
            'recipe': self._recipe,
            'cost': self._cost,
            'price': self._price,
            'order_time': self._order_time,
            'finish_time': self._finish_time
        }


def simulate(
        env: Environment,
        sys: Dict
):
    def get_order(x: int, order_time: int) -> Generator[Event, Any, Any]:
        pizza = Pizza(x, order_time, sys['RECIPE'], sys['COSTS'])
        yield env.timeout(pizza.order_time)

        with sys['CAPACITY'].request() as request:
            yield request
            yield env.process(kitchen.bake(env, pizza))

    kitchen = Kitchen(sys)
    kitchen.set_oven_time(sys['OVEN_TIME'])

    order_n = 0
    orders = sum(sys['ORDERS'])

    uniform_t = uniform(0, sys['HOURS']*60 - sys['OVEN_TIME'], orders)
    uniform_t = uniform_t.astype(int)
    uniform_t.sort()

    for n in range(orders):
        order_n += 1
        order_t = uniform_t[n]
        env.process(get_order(order_n, order_t))

        yield env.timeout(0)


def run(
        data: List[Dict],
        capacity: int = 2,
        hours: int = 8,
        lam: int = 12,
        oven_time: int = 12,
        flour: float = 0.13,
        salt: float = 0.13,
        yeast: float = 2.16,
        water: float = 0.00,
        olive_oil: float = 0.38,
        sauce: float = 0.16,
        cheese: float = 0.50

) -> None:
    env = Environment()

    system = {
        'DATA': [],
        'CAPACITY': Resource(env, capacity),
        'HOURS': hours,
        'ORDERS': poisson(lam, hours),
        'OVEN_TIME': oven_time,
        'RECIPE': {
            'flour': 7,
            'salt': 0.17,
            'yeast': 0.07,
            'water': 4.75,
            'olive_oil': 0.125,
            'sauce': 6,
            'cheese': 6
        },
        'COSTS': {
            'flour': flour,
            'salt': salt,
            'yeast': yeast,
            'water': water,
            'olive_oil': olive_oil,
            'sauce': sauce,
            'cheese': cheese
        }
    }

    system['COUNTS'] = sum(system['ORDERS'])

    env.process(simulate(env, system))
    env.run(until=60*8)

    data.append(system['DATA'])


def compile_results(results: List, output: str) -> None:
    data = []
    n = len(results)

    for i in range(n):
        for obj in results[i]:
            row = obj.get_data()
            row['iteration'] = i
            data.append(row)

    results = DataFrame(data)
    results.to_csv(output + '_results.csv', index=False)
