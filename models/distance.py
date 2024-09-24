from collections import defaultdict


def get_parental_bond_weight(n):
    try:
        return n.parental_bond.weight
    except AttributeError:
        return 0


def different_tier_weighted_reduce(n1, n2):
    target_tier = min(n1.tier, n2.tier)
    current_n, other_n = (n1, n2) if n1.tier > n2.tier else (n2, n1)

    distance = 0
    while current_n.tier > target_tier:
        distance += get_parental_bond_weight(current_n)
        current_n = current_n.parent
    return current_n, other_n, distance



# recurent alternative
# def different_tier_weighted_reduce(n1, n2, cache):
#     if n1.tier == n2.tier:
#         return 0
#     current_n, other_n = (n1, n2) if n1.tier > n2.tier else (n2, n1)
#     d = get_parental_bond_weight(current_n)
#     return d + different_tier_weighted_reduce(current_n.parent, other_n, cache)



def count_weighted_distance(n1, n2, cache):
    if n1 == n2:
        return 0

    if (distance := cache.get(n1, n2)) is not None:
        return distance

    if n1.tier == n2.tier:
        distance = (get_parental_bond_weight(n1) +
                    get_parental_bond_weight(n2) +
                    count_weighted_distance(n1.parent, n2.parent, cache))
        cache.update(n1, n2, distance)
        return distance
    else:
        n1, n2, d = different_tier_weighted_reduce(n1, n2)
        distance = d + count_weighted_distance(n1, n2, cache)
        cache.update(n1, n2, distance)
        return distance


def different_tier_nonweighted_reduce(n1, n2):
    delta_tier = abs(n1.tier - n2.tier)
    target_tier = min(n1.tier, n2.tier)
    current_n, other_n = (n1, n2) if n1.tier > n2.tier else (n2, n1)
    while current_n.tier > target_tier:
        current_n = current_n.parent
    return current_n, other_n, delta_tier


def count_nonweighted_distance(n1, n2, cache):
    if n1 == n2:
        return 0

    if (distance := cache.get(n1, n2)) is not None:
        return distance

    if n1.tier == n2.tier:
        distance = 2 + count_nonweighted_distance(n1.parent, n2.parent, cache)
        cache.update(n1, n2, distance)
        return distance
    else:
        n1, n2, d = different_tier_nonweighted_reduce(n1, n2)
        distance = d + count_nonweighted_distance(n1, n2, cache)
        cache.update(n1, n2, distance)
        return distance


def count_distance(n1, n2, cache, weighted=True):
    if weighted:
        return count_weighted_distance(n1, n2, cache)
    else:
        return count_nonweighted_distance(n1, n2, cache)


class DistanceCache:
    def __init__(self):
        self.d = defaultdict(dict)

    def get(self, n1, n2):
        distance = self.d[n1].get(n2)
        if distance is None:
            return self.d[n2].get(n1)

    def update(self, n1, n2, distance):
        self.d[n1][n2] = distance
        self.d[n2][n1] = distance


class DistanceCounter:
    def __init__(self, weighted=True):
        self.cache = DistanceCache()
        self.weighted = weighted

    def distance(self, n1, n2):
        return count_distance(n1, n2, self.cache, self.weighted)
