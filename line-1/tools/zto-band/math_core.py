"""Integer Uniswap v4 single-interval math. No floating point or dependencies.

Tick factors and rounding follow Uniswap v4-core TickMath/SqrtPriceMath/SwapMath
(MIT; see LICENSE-Uniswap.txt and README links). This does not traverse ticks.
"""

Q96 = 1 << 96
MILLION = 1_000_000
FACTORS = tuple(int(s, 16) for s in (
    'fffcb933bd6fad37aa2d162d1a594001', 'fff97272373d413259a46990580e213a',
    'fff2e50f5f656932ef12357cf3c7fdcc', 'ffe5caca7e10e4e61c3624eaa0941cd0',
    'ffcb9843d60f6159c9db58835c926644', 'ff973b41fa98c081472e6896dfb254c0',
    'ff2ea16466c96a3843ec78b326b52861', 'fe5dee046a99a2a811c461f1969c3053',
    'fcbe86c7900a88aedcffc83b479aa3a4', 'f987a7253ac413176f2b074cf7815e54',
    'f3392b0822b70005940c7a398e4b70f3', 'e7159475a2c29b7443b29c7fa6e889d9',
    'd097f3bdfd2022b8845ad8f792aa5825', 'a9f746462d870fdf8a65dc1f90e061e5',
    '70d869a156d2a1b890bb3df62baf32f7', '31be135f97d08fd981231505542fcfa6',
    '9aa508b5b7a84e1c677de54f3e99bc9', '5d6af8dedb81196699c329225ee604',
    '2216e584f5fa1ea926041bedfe98', '48a170391f7dc42444e8fa2',
))


def ceil_div(n, d):
    return (n + d - 1) // d


def sqrt_at_tick(tick):
    if type(tick) is not int or not -887272 <= tick <= 887272:
        raise ValueError('tick outside Uniswap range')
    ratio = 1 << 128
    for bit, factor in enumerate(FACTORS):
        if abs(tick) & (1 << bit):
            ratio = (ratio * factor) >> 128
    if tick > 0:
        ratio = ((1 << 256) - 1) // ratio
    return ceil_div(ratio, 1 << 32)


def amount0(a, b, liquidity, up=False):
    a, b = sorted((a, b))
    n, d = liquidity * Q96 * (b - a), a * b
    return ceil_div(n, d) if up else n // d


def amount1(a, b, liquidity, up=False):
    n = liquidity * abs(b - a)
    return ceil_div(n, Q96) if up else n // Q96


def total_fee(packed_protocol, lp_fee, zero_for_one):
    protocol = (packed_protocol & 4095) if zero_for_one else (packed_protocol >> 12)
    if not 0 <= protocol <= 1000 or not 0 <= lp_fee < MILLION:
        raise ValueError('unsupported fee')
    return protocol + lp_fee - protocol * lp_fee // MILLION


def interior_target(tick, spacing, zero_for_one):
    """Stop one Q96 unit inside the nearest possible initialized boundary."""
    low = (tick // spacing) * spacing
    edge = max(-887272, low) if zero_for_one else min(887272, low + spacing)
    return sqrt_at_tick(edge) + (1 if zero_for_one else -1), edge


def capacity(price, target, liquidity, fee, zero_for_one):
    if liquidity <= 0 or (target >= price if zero_for_one else target <= price):
        return 0
    net = (amount0 if zero_for_one else amount1)(price, target, liquidity, True)
    return net + ceil_div(net * fee, MILLION - fee)


def swap_step(price, target, liquidity, fee, gross, zero_for_one):
    """One exact-input step; report unused input when target is reached."""
    if gross < 0 or gross >= 1 << 255 or liquidity <= 0:
        raise ValueError('input/liquidity out of range')
    if not 0 <= fee < MILLION:
        raise ValueError('unsupported fee')
    if target >= price if zero_for_one else target <= price:
        raise ValueError('no room inside this tick interval in the requested direction')
    net_available = gross * (MILLION - fee) // MILLION
    net_to_target = (amount0 if zero_for_one else amount1)(price, target, liquidity, True)
    if net_available >= net_to_target:
        nxt = target
        net = net_to_target
        charged_fee = ceil_div(net * fee, MILLION - fee)
    else:
        net = net_available
        if zero_for_one:
            numerator = liquidity * Q96
            # Match the uint256 overflow fallback used by SqrtPriceMath.
            product = net * price
            if product < 1 << 256 and numerator + product < 1 << 256:
                nxt = ceil_div(numerator * price, numerator + product)
            else:
                nxt = ceil_div(numerator, numerator // price + net)
        else:
            nxt = price + net * Q96 // liquidity
        charged_fee = gross - net
    output = (amount1 if zero_for_one else amount0)(price, nxt, liquidity)
    return {'sqrt_price_after_x96': str(nxt), 'input_to_pool_raw': str(net),
            'fee_raw': str(charged_fee), 'input_consumed_raw': str(net + charged_fee),
            'input_unspent_raw': str(gross - net - charged_fee), 'output_raw': str(output)}
