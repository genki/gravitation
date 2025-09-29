
from __future__ import annotations
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from gw_models import PolarizationStackModel, MemoryStackModel
from solar_conjunction import AchromaticShapiroResidualModel
from frb_lens_blur import FRBAchromaticBlurModel
from pta_shape import PTACorrelationShapeTest
from common import R_sun, AU

def demo():
    rows = []
    # A1: GW polarization stacking
    pol = PolarizationStackModel(Gpol=0.4)
    snr_each = 20.0
    sigma_target = 0.01  # 1% non-TT limit
    n_events = pol.required_events(target_sigma=sigma_target, snr_per_event=snr_each)
    rows.append(dict(test="GW polarization", metric="events for 1% limit", value=n_events, unit="events"))

    # A2: Memory stacking
    mem = MemoryStackModel(rho_thresh=5.0)
    m_single = 0.5  # assumed per-event memory SNR from a pipeline (placeholder)
    n_mem = mem.required_events(m_single=m_single)
    rows.append(dict(test="GW memory", metric="events for 5σ stack (m_single=0.5)", value=n_mem, unit="events"))

    # B: Solar conjunction achromatic residual
    sc = AchromaticShapiroResidualModel(sigma0_ps=5.0, xi_ps_Rsun2=20.0)  # choose a small xi for illustration
    b_list = np.array([3,5,10,20,50]) * R_sun
    sigs = sc.sigma_ps(b_list)
    for b, s in zip(b_list, sigs):
        rows.append(dict(test="Solar conjunction", metric=f"RMS at b={b/R_sun:.0f} R_sun", value=s, unit="ps"))

    # C: FRB achromatic blur
    frb = FRBAchromaticBlurModel(tau0_us=50.0)
    kappa_vals = np.array([0.1, 0.2, 0.5, 1.0])
    tau_us = frb.tau_achr_us(kappa_vals)
    z = [frb.detectability(t, time_resolution_us=20.0, snr_pulse=100.0) for t in tau_us]
    rows.append(dict(test="FRB blur", metric="tau_achr at kappa=0.5", value=tau_us[2], unit="µs"))
    rows.append(dict(test="FRB blur", metric="Z-score (kappa=0.5, dt=20µs, SNR=100)", value=z[2], unit="σ"))

    # D: PTA correlation shape
    pta = PTACorrelationShapeTest(f_nonTT=0.02)
    theta = np.linspace(1e-3, np.pi - 1e-3, 512)
    rms_dev = pta.rms_shape_deviation(theta, alt='flat')
    # assume per-pair correlation error ~0.05 as an order-of-magnitude figure
    n_pairs = pta.required_pairs(rms_dev=rms_dev, sigma_pair=0.05)
    rows.append(dict(test="PTA shape", metric="required distinct pairs (σ_pair=0.05)", value=n_pairs, unit="pairs"))

    df = pd.DataFrame(rows)
    print(df.to_string(index=False))

    # Quick plots: Solar conjunction residual vs b
    plt.figure()
    plt.loglog(b_list / R_sun, sigs, marker='o')
    plt.xlabel("impact parameter b / R_sun")
    plt.ylabel("achromatic RMS [ps]")
    plt.title("Solar conjunction achromatic residual (illustrative)")
    plt.tight_layout()
    plt.savefig("solar_residual_demo.png", dpi=140)

    # PTA shape deviation vs f_nonTT
    fvals = np.linspace(0.0, 0.05, 51)
    rms_list = []
    for f in fvals:
        pta = PTACorrelationShapeTest(f_nonTT=float(f))
        rms_list.append(pta.rms_shape_deviation(theta, alt='flat'))
    plt.figure()
    plt.plot(fvals, rms_list)
    plt.xlabel("non-TT admixture f")
    plt.ylabel("RMS shape deviation")
    plt.title("PTA correlation: RMS deviation vs f (flat alt-shape)")
    plt.tight_layout()
    plt.savefig("pta_rms_vs_f.png", dpi=140)

if __name__ == "__main__":
    demo()
