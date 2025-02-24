"""Aero library inspried by @ProfHoekstra/bluesky.

Functions for aeronautics in this module
    - physical quantities always in SI units
    - lat,lon,course and heading in degrees

International Standard Atmosphere
    p,rho,T = atmos(h)    # atmos as function of geopotential altitude h [m]
    a = vsound(h)         # speed of sound [m/s] as function of h[m]
    p = pressure(h)       # calls atmos but retruns only pressure [Pa]
    T = temperature(h)    # calculates temperature [K]
    rho = density(h)      # calls atmos but retruns only density [kg/m3]

Speed conversion at altitude h[m] in ISA:
    mach = tas2mach(v_tas,h)    # true airspeed (v_tas) to mach number conversion
    v_tas = mach2tas(mach,h)    # true airspeed (v_tas) to mach number conversion
    v_tas = eas2tas(v_eas,h)     # equivalent airspeed to true airspeed, h in [m]
    v_eas = tas2eas(v_tas,h)     # true airspeed to equivent airspeed, h in [m]
    v_tas = cas2tas(v_cas,h)     # v_cas  to v_tas conversion both m/s, h in [m]
    v_cas = tas2cas(v_tas,h)     # v_tas to v_cas conversion both m/s, h in [m]
    v_cas = mach2cas(mach,h)    # mach to v_cas conversion v_cas in m/s, h in [m]
    mach   = cas2mach(v_cas,h)  # v_cas to mach copnversion v_cas in m/s, h in [m]
"""

import numpy as np

"""Aero and Geo Constants """
kts = 0.514444      # knot -> m/s
ft = 0.3048         # ft -> m
fpm = 0.00508       # ft/min -> m/s
inch = 0.0254       # inch -> m
sqft = 0.09290304   # 1 square foot
nm = 1852.          # nautical mile -> m
lbs = 0.453592      # pound -> kg
g0 = 9.80665        # m/s2, Sea level gravity constant
R = 287.05287       # m2/(s2 x K), gas constant, sea level ISA
p0 = 101325.        # Pa, air pressure, sea level ISA
rho0 = 1.225        # kg/m3, air density, sea level ISA
T0 = 288.15         # K, temperature, sea level ISA
gamma = 1.40        # cp/cv for air
gamma1 = 0.2        # (gamma-1)/2 for air
gamma2 = 3.5        # gamma/(gamma-1) for air
beta = -0.0065      # [K/m] ISA temp gradient below tropopause
r_earth = 6371000.  # m, average earth radius
a0 = 340.293988     # m/s, sea level speed of sound ISA, sqrt(gamma*R*T0)


def atmos(h):
    """Compute press, density and temperature at a given altitude.

    Args:
        h (float or ndarray): Altitude (in meters).

    Returns:
        (float, float, float) or (ndarray, ndarray, ndarray):
            Air pressure (Pa), density (kg/m3), and temperature (K).

    """
    T = np.maximum(288.15 - 0.0065 * h, 216.65)
    rhotrop = 1.225 * (T / 288.15)**4.256848030018761
    dhstrat = np.maximum(0., h - 11000.0)
    rho = rhotrop * np.exp(-dhstrat / 6341.552161)
    p = rho * R * T
    return p, rho, T


def temperature(h):
    """Compute air temperature at a given altitude.

    Args:
        h (float or ndarray): Altitude (in meters).

    Returns:
        float or ndarray: Air temperature (K).

    """
    p, r, T = atmos(h)
    return T


def pressure(h):
    """Compute air pressure at a given altitude.

    Args:
        h (float or ndarray): Altitude (in meters).

    Returns:
        float or ndarray: Air pressure (Pa).

    """
    p, r, T = atmos(h)
    return p


def density(h):
    """Compute air density at a given altitude.

    Args:
        h (float or ndarray): Altitude (in meters).

    Returns:
        float or ndarray: Air density (kg/m3).

    """
    p, r, T = atmos(h)
    return r


def vsound(h):
    """Compute speed of sound at a given altitude.

    Args:
        h (float or ndarray): Altitude (in meters).

    Returns:
        float or ndarray: speed of sound (m/s).

    """
    T = temperature(h)
    a = np.sqrt(gamma * R * T)
    return a


def distance(lat1, lon1, lat2, lon2, h=0):
    """Compute distance between two (or two series) of coordinates using Harversine formula.

    Args:
        lat1 (float or ndarray): Starting latitude (in degrees).
        lon1 (float or ndarray): Starting longitude (in degrees).
        lat2 (float or ndarray): Ending latitude (in degrees).
        lon2 (float or ndarray): Ending longitude (in degrees).
        h (float or ndarray): Altitude (in meters). Defaults to 0.

    Returns:
        float or ndarray: Distance (in meters).

    """
    # convert decimal degrees to radians
    lat1 = np.radians(lat1)
    lon1 = np.radians(lon1)
    lat2 = np.radians(lat2)
    lon2 = np.radians(lon2)

    # haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
    c = 2 * np.arcsin(np.sqrt(a))
    dist = c * (r_earth + h)   # meters, radius of earth
    return dist


def bearing(lat1, lon1, lat2, lon2):
    """Compute the bearing between two (or two series) of coordinates.

    Args:
        lat1 (float or ndarray): Starting latitude (in degrees).
        lon1 (float or ndarray): Starting longitude (in degrees).
        lat2 (float or ndarray): Ending latitude (in degrees).
        lon2 (float or ndarray): Ending longitude (in degrees).

    Returns:
        float or ndarray: Bearing (in degrees). Between 0 and 360.

    """
    lat1 = np.radians(lat1)
    lon1 = np.radians(lon1)
    lat2 = np.radians(lat2)
    lon2 = np.radians(lon2)
    x = np.sin(lon2-lon1) * np.cos(lat2)
    y = np.cos(lat1) * np.sin(lat2) \
        - np.sin(lat1) * np.cos(lat2) * np.cos(lon2-lon1)
    initial_bearing = np.arctan2(x, y)
    initial_bearing = np.degrees(initial_bearing)
    bearing = (initial_bearing + 360) % 360
    return bearing


def tas2mach(v_tas, h):
    """Convert true airspeed to mach number at a given altitude.

    Args:
        v_tas (float or ndarray): True airspeed (m/s).
        h (float or ndarray): Altitude (m).

    Returns:
        float or ndarray: mach number.

    """
    a = vsound(h)
    mach = v_tas/a
    return mach


def mach2tas(mach, h):
    """Convert mach number to true airspeed at a given altitude.

    Args:
        mach (float or ndarray): Mach number.
        h (float or ndarray): Altitude (m).

    Returns:
        float or ndarray: True airspeed (m/s).

    """
    a = vsound(h)
    v_tas = mach*a
    return v_tas


def eas2tas(v_eas, h):
    """Convert equivalent airspeed to true airspeed at a given altitude.

    Args:
        v_eas (float or ndarray): Equivalent airspeed (m/s).
        h (float or ndarray): Altitude (m).

    Returns:
        float or ndarray: True airspeed (m/s).

    """
    rho = density(h)
    v_tas = v_eas * np.sqrt(rho0/rho)
    return v_tas


def tas2eas(v_tas, h):
    """Convert true airspeed to equivalent airspeed at a given altitude.

    Args:
        v_tas (float or ndarray): True airspeed (m/s).
        h (float or ndarray): Altitude (m).

    Returns:
        float or ndarray: Equivalent airspeed (m/s).

    """
    rho = density(h)
    v_eas = v_tas * np.sqrt(rho/rho0)
    return v_eas


def cas2tas(v_cas, h):
    """Convert calibrated airspeed to true airspeed at a given altitude.

    Args:
        v_cas (float or ndarray): Equivalent airspeed (m/s).
        h (float or ndarray): Altitude (m).

    Returns:
        float or ndarray: True airspeed (m/s).

    """
    p, rho, T = atmos(h)
    qdyn = p0*((1.+rho0*v_cas*v_cas/(7.*p0))**3.5-1.)
    v_tas = np.sqrt(7.*p/rho*((1.+qdyn/p)**(2./7.)-1.))
    return v_tas


def tas2cas(v_tas, h):
    """Convert true airspeed to calibrated airspeed at a given altitude.

    Args:
        v_tas (float or ndarray): True airspeed (m/s).
        h (float or ndarray): Altitude (m).

    Returns:
        float or ndarray: Calibrated airspeed (m/s).

    """
    p, rho, T = atmos(h)
    qdyn = p*((1.+rho*v_tas*v_tas/(7.*p))**3.5-1.)
    v_cas = np.sqrt(7.*p0/rho0*((qdyn/p0+1.)**(2./7.)-1.))
    return v_cas


def mach2cas(mach, h):
    """Convert mach number to calibrated airspeed at a given altitude.

    Args:
        mach (float or ndarray): Mach number.
        h (float or ndarray): Altitude (m).

    Returns:
        float or ndarray: Calibrated airspeed (m/s).

    """
    v_tas = mach2tas(mach, h)
    v_cas = tas2cas(v_tas, h)
    return v_cas


def cas2mach(v_cas, h):
    """Convert calibrated airspeed to mach number  at a given altitude.

    Args:
        v_cas (float or ndarray): Calibrated airspeed (m/s).
        h (float or ndarray): Altitude (m).

    Returns:
        float or ndarray: Mach number.

    """
    v_tas = cas2tas(v_cas, h)
    mach = tas2mach(v_tas, h)
    return mach


def crossover_alt(v_cas, mach):
    """Conver the crossover altitude given constant CAS and Mach.

    Args:
        v_cas (float or ndarray): Calibrated airspeed (m/s).
        mach (float or ndarray): Mach number.

    Returns:
        float or ndarray: Altitude (m).

    """
    delta = ((0.2*(v_cas/a0)**2 + 1)**3.5 - 1) / ((0.2 * mach**2 + 1)**3.5 - 1)
    h = T0 / beta * (delta ** (-1 * R * beta / g0) -1)
    return h
