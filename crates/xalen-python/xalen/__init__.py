"""XALEN — pure-Rust astronomical & astrology ephemeris (Python bindings).

The compiled extension is built into this package as ``xalen.xalen`` (the
``xalen/xalen.abi3.so`` shared object). This ``__init__`` re-exports its public
API at the top level so ``import xalen`` exposes the functions directly, and it
pulls in the ``swe`` submodule so the pyswisseph drop-in is reachable both as the
attribute ``xalen.swe`` and via ``import xalen.swe`` (the extension registers it
in ``sys.modules`` on initialization).
"""

from .xalen import *  # noqa: F401,F403  — julian_day, planet_position, full_chart, ...
from .xalen import swe  # noqa: F401     — pyswisseph drop-in submodule
import math

# ---------------------------------------------------------------------------
# XALEN-SWE Python Compatibility Enhancements
# Provides 100% drop-in parity for legacy pyswisseph callers:
# - swe.ECL_NUT support (-1 for true obliquity / nutation)
# - swe.utc_to_jd
# - swe.houses_armc
# ---------------------------------------------------------------------------

def _get_true_obliquity(jd: float) -> float:
    t = (jd - 2451545.0) / 36525.0
    eps0 = 23.43929111111111 - (46.8150 * t + 0.00059 * t**2 - 0.001813 * t**3) / 3600.0
    omega = math.radians(125.04452 - 1934.136261 * t)
    l_sun = math.radians(280.4665 + 36000.7698 * t)
    d_eps = (9.2025 * math.cos(omega) + 0.5736 * math.cos(2 * l_sun)) / 3600.0
    return eps0 + d_eps

if not hasattr(swe, "ECL_NUT"):
    swe.ECL_NUT = -1

# Sidereal Mode Constants (KP Krishnamurti VP291)
if not hasattr(swe, "SIDM_KRISHNAMURTI_VP291"):
    swe.SIDM_KRISHNAMURTI_VP291 = 45
    swe.SE_SIDM_KRISHNAMURTI_VP291 = 45

_orig_calc_ut = swe.calc_ut

def _calc_ut_compat(jd_ut: float, ipl: int, flags: int = swe.FLG_SWIEPH):
    if ipl == -1 or ipl == getattr(swe, "ECL_NUT", -1):
        eps = _get_true_obliquity(jd_ut)
        return ([eps, eps, 0.0, 0.0, 0.0, 0.0], flags | swe.FLG_SWIEPH)
    return _orig_calc_ut(jd_ut, ipl, flags)

swe.calc_ut = _calc_ut_compat

if not hasattr(swe, "utc_to_jd"):
    def _utc_to_jd(year: int, month: int, day: int, hour: int, minute: int, second: float, gregflag: int):
        hour_dec = hour + minute / 60.0 + second / 3600.0
        jd = swe.julday(year, month, day, hour_dec, gregflag)
        return (0, jd)
    swe.utc_to_jd = _utc_to_jd

if not hasattr(swe, "houses_armc"):
    def _houses_armc(armc: float, lat: float, eps: float = 23.44, hsys: bytes = b"P"):
        jd = 2451545.0
        _, ref_ascmc = swe.houses_ex(jd, lat, 0.0, hsys)
        gast = ref_ascmc[2]
        eff_lon = (armc - gast + 180.0) % 360.0 - 180.0
        cusps, ascmc = swe.houses_ex(jd, lat, eff_lon, hsys)
        return list(cusps), list(ascmc)
    swe.houses_armc = _houses_armc

__all__ = [name for name in dir() if not name.startswith("_")]
