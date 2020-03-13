import multiprocessing as mp
import numpy as np
import exoplanet as xo
import pymc3 as pm

from subprocess import call

from matplotlib import pyplot as plt

try:
    from statsmodels.robust import scale as sc
except:
    print('[INFO] Need to install `statsmodels` from acquire `scale.mad`')
    command = 'pip install statsmodels'
    call(command.split())
    from statsmodels.robust import scale as sc

try:
    from exomast_api import exoMAST_API
except:
    print('[INFO] Need to install `exomast_api` from acquire planet info')
    command = 'pip install git+https://github.com/exowanderer/exomast_api'
    call(command.split())
    from exomast_api import exoMAST_API

try:
    import colorednoise as cn
except:
    print('[INFO] Need to install `colorednoise` to generate pink noise')
    command = 'pip install colorednoise'
    call(command.split())
    import colorednoise as cn

plt.ion()


def build_gp_pink_noise_formulaic(times, data, dataerr,
                                  log_Q=np.log(1.0 / np.sqrt(2))):
    ''' Build a pink noise GP iterating over S0, w0, s2
         and then computing Sw4 = S0 * w**4

        times (nDarray): time stamps for x-array
        data (nDarray): normalized flux for transit light curve
        dataerr (nDarray): uncertainty values per data point
        log_Q (float): hyperparameter for SHO kernel [Q=1/sqrt(2): pink noise]
    '''
    log_S0 = pm.Normal("log_S0", mu=0.0, sigma=15.0,
                       testval=np.log(np.var(data)))
    log_w0 = pm.Normal("log_w0", mu=0.0, sigma=15.0,
                       testval=np.log(3.0))
    log_Sw4 = pm.Deterministic(
        "log_variance_r", log_S0 + 4 * log_w0)

    log_s2 = pm.Normal("log_variance_w", mu=0.0, sigma=15.0,
                       testval=np.log(np.var(data)))

    kernel = xo.gp.terms.SHOTerm(
        log_Sw4=log_Sw4, log_w0=log_w0, log_Q=log_Q)

    gp = xo.gp.GP(kernel, times, dataerr ** 2 + pm.math.exp(log_s2))

    return gp


def build_gp_pink_noise(times, data, dataerr,
                        log_Q=np.log(1.0 / np.sqrt(2))):
    ''' Build a pink noise GP iterating over S0, w0, Sw4


        times (nDarray): time stamps for x-array
        data (nDarray): normalized flux for transit light curve
        dataerr (nDarray): uncertainty values per data point
        log_Q (float): hyperparameter for SHO kernel [Q=1/sqrt(2): pink noise]
    '''
    log_w0 = pm.Normal("log_w0", mu=0.0, sigma=15.0,
                       testval=np.log(3.0))
    log_Sw4 = pm.Normal("log_variance_r", mu=0.0, sigma=15.0,
                        testval=np.log(np.var(data)))
    log_s2 = pm.Normal("log_variance_w", mu=0.0, sigma=15.0,
                       testval=np.log(np.var(data)))

    kernel = xo.gp.terms.SHOTerm(
        log_Sw4=log_Sw4, log_w0=log_w0, log_Q=log_Q)

    return xo.gp.GP(kernel, times, dataerr ** 2 + pm.math.exp(log_s2))


def run_pymc3_with_gp(times, data, dataerr, orbit,
                      log_Q=np.log(1 / np.sqrt(2)),
                      tune=5000, draws=5000,
                      target_accept=0.9, u=[0]):
    ''' Build a PyMC3 model with RpRs (`r`), `mean`, and GP model

        times (nDarray): time stamps for x-array
        data (nDarray): normalized flux for transit light curve
        dataerr (nDarray): uncertainty values per data point
        log_Q (float): hyperparameter for SHO kernel [Q=1/sqrt(2): pink noise]
        tune (int): number of tuning iterations for `pm.sample`
        draw (int): number of iterations to draw for `pm.sample`
        target_accept (float): target acceptance ratio for `pm.sample`
        u (list): list of limb darkening parameters; default: no limb darkening
    '''
    # Create the PyMC3 model
    with pm.Model() as model:

        # The baseline flux
        mean = pm.Normal("mean", mu=0.0, sd=1.0)
        r = pm.Uniform("r", lower=0.0, upper=0.5, testval=0.15)

        # Compute the model light curve using starry
        light_curves = xo.LimbDarkLightCurve(u).get_light_curve(
            orbit=orbit, r=r, t=times
        )
        light_curve = pm.math.sum(light_curves, axis=-1) + mean

        # Here we track the value of the model light curve for plotting
        # purposes
        pm.Deterministic("light_curves", light_curves)

        # The likelihood function assuming known Gaussian uncertainty
        pm.Normal("obs", mu=light_curve, sd=dataerr, observed=data)

        gp = build_gp_pink_noise(times, data, dataerr, log_Q=log_Q)
        gp.marginal("gp", observed=data)

        # Fit for the maximum a posteriori parameters given the simuated
        # dataset
        map_soln = xo.optimize(start=model.test_point)

        trace = None  # Default to None
        if run_mcmc:
            # # MCMC the posterior distribution
            # with pm.Model() as model:
            np.random.seed(42)
            trace = pm.sample(
                tune=tune,
                draws=tune,
                start=map_soln,
                chains=mp.cpu_count(),
                step=xo.get_dense_nuts_step(target_accept=target_accept),
                cores=mp.cpu_count()
            )

        return trace, map_soln, model


def build_synthetic_model(min_phase=-0.1, max_phase=0.1, size=1000,
                          planet_name='HD 189733 b', u=[0.0]):
    ''' Create synthetic transit light curve by grabbing data from exo.mast
         and populating xo.orbits.KeplerianOrbit with that

        min_phase (float): minimum value for the transit light curve phase
        max_phase (float): maximum value for the transit light curve phase
        size (int): number of data points
        planet_name (str): exo.mast planet name to look up and use to populate
        u (list): limb darkening coefficients; default: no limb darkening
    '''
    # Planetary orbital parameters
    planet = exoMAST_API(planet_name)

    deg2rad = np.pi / 180
    orbit = xo.orbits.KeplerianOrbit(
        t0=planet.transit_time,  # 54278.93671400007
        period=planet.orbital_period,  # 2.21857567
        a=planet.a_Rs,  # 8.83602
        # b=planet.impact_parameter,  # 0.6631
        # incl=planet.inclination * deg2rad,  # 1.4959217018843398
        duration=planet.transit_duration,  # 0.0759722
        ecc=planet.eccentricity,  # 0.0
        omega=planet.omega * deg2rad,  # 1.5707963267948966 == pi/2
    )

    star = xo.LimbDarkLightCurve(u)
    phase = np.linspace(min_phase, max_phase, size)
    times = phase * planet.orbital_period + t0
    model = star.get_light_curve(
        r=planet.Rp_Rs,
        orbit=orbit,
        t=times)

    model = model.eval().flatten()

    return times, model, orbit


def build_fake_data(sigma_ratio=0.1, size=1000):
    ''' Use `build_synthetic_model` + `colornoise.powerlaw_psd_gaussian`
         to create a synthtic_model with pink noise

        sigma_ratio (float): ratio between sigma_w and sigma_r
        size (int): number of data points to sample
    '''

    ppm = 1e6

    std_gauss = 50 / ppm
    dataerr = np.random.uniform(-5, 5, size) / ppm + std_gauss
    times, synthetic_eclipse, _ = build_synthetic_model(size=size)

    pink_noise = cn.powerlaw_psd_gaussian(  # pink noise
        exponent=1, size=size)

    mad2std = 1.482601669
    med_noise = np.median(pink_noise)
    std_noise = sc.mad(pink_noise) * mad2std

    pink_noise = (pink_noise - med_noise) / std_noise * std_gauss * sigma_ratio
    data = np.random.normal(synthetic_eclipse, dataerr) + pink_noise

    return times, data, dataerr


def plot_results(map_soln, times, data, dataerr):
    ''' Matplotlib wrapper to plot the MAP solution

        map_soln (object): output of `xo.optimize`
        times (nDarray): time stamps for x-array
        data (nDarray): normalized flux for transit light curve
        dataerr (nDarray): uncertainty values per data point
    '''

    plt.errorbar(times, data, dataerr, fmt='o', color='C0', ms=1)
    plt.plot(times, map_soln["light_curves"].flatten(),
             color='C1', lw=2, label="MAP Soln")

    plt.xlim(times.min(), times.max())
    plt.ylabel("relative flux")
    plt.xlabel("time [days]")
    plt.legend(fontsize=10)
    _ = plt.title("map model")


def plot_corner(trace, planet):
    ''' Wrapper for corner.corner

        trace (object): output of `pm.sample`
        planet (object): output of `exoMAST_API`
    '''
    import corner

    RpRs = planet.Rp_Rs
    mean = 0.0

    samples = pm.trace_to_dataframe(trace)

    varnames = [name for name in samples.columns if 'light_curves' not in name]

    _ = corner.corner(
        samples[varnames],
        bins=20,
        color='C0',
        smooth=True,
        smooth1d=True,
        labels=varnames,
        show_titles=True,
        truths=None,
        truth_color='C1',
        scale_hist=True,
    )


if __name__ == '__main__':
    ''' (1) Generate `n_pts` data points with a syntethic model + pink noise
        (2) Create PyMC3 model with that data
        (3) Solve for the MAP of that model over the data
        (4) Sample the posterior with and MCCM of that model over the data
        (5) Plot the results
        (6) Generate the corner plot over the MCMC samples
    '''

    # Create the synthetic model + noisy data
    n_pts = 1000
    times, synthetic_eclipse, orbit = build_synthetic_model(size=n_pts)
    times, data, dataerr = build_fake_data()

    # PyMC3 parameters
    log_Q = 1 / np.sqrt(2),
    tune = 100,
    draws = 100,
    target_accept = 0.9

    # Create the PyMC3 model + MAP solution + MCMC samples
    trace, map_soln, pm_model = run_pymc3_with_gp(times, data, dataerr, orbit,
                                                  log_Q=np.log(1 / np.sqrt(2)),
                                                  tune=5000, draws=5000,
                                                  target_accept=0.9)

    # Plot the light curve results
    plot_results(map_soln, times, data, dataerr)

    # Generate the corner plot over the posterior
    plot_corner(trace, planet)
