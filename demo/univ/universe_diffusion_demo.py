"""Minimal training-free 'cosmic' diffusion-style demo.

This script starts from pure Gaussian noise (BigBang) and iteratively applies
hand-crafted energy gradients plus annealed noise so that a smooth, planet-like
pattern gradually emerges. No datasets or learned weights are used.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

import matplotlib.pyplot as plt
import numpy as np
import torch


@dataclass
class UniverseConfig:
    image_size: int = 64
    T: int = 400  # number of reverse steps
    alpha_max: float = 0.35
    beta_max: float = 0.25
    w_smooth_max: float = 2.0
    w_center_max: float = 1.5
    w_circle_max: float = 1.25
    circle_radius: float = 0.32  # normalized (0–1) radius of bright ring/planet edge
    circle_width: float = 0.08
    seed: int = 42
    save_interval: int = 40  # save every N steps
    device: str = "cuda" if torch.cuda.is_available() else "cpu"


def set_seed(seed: int) -> None:
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def init_state(cfg: UniverseConfig) -> torch.Tensor:
    """Generate initial BigBang noise."""
    x = torch.randn(1, 1, cfg.image_size, cfg.image_size, device=cfg.device)
    return x


def _radius_grid(h: int, w: int, device: str) -> torch.Tensor:
    """Precompute normalized radius map centered at the image middle."""
    ys, xs = torch.meshgrid(
        torch.linspace(-1.0, 1.0, h, device=device),
        torch.linspace(-1.0, 1.0, w, device=device),
        indexing="ij",
    )
    r = torch.sqrt(xs * xs + ys * ys)
    return r.clamp(max=1.0)


def E_smooth(x: torch.Tensor) -> torch.Tensor:
    dx = x[:, :, :, 1:] - x[:, :, :, :-1]
    dy = x[:, :, 1:, :] - x[:, :, :-1, :]
    return (dx.square().mean() + dy.square().mean())


def E_center(x: torch.Tensor, r_norm: torch.Tensor) -> torch.Tensor:
    # Encourage brightness near center (small r) by penalizing brightness far away.
    return (r_norm * x.squeeze(1)).mean()


def E_circle(
    x: torch.Tensor, r_norm: torch.Tensor, cfg: UniverseConfig
) -> torch.Tensor:
    ring = torch.exp(-((r_norm - cfg.circle_radius) ** 2) / (2 * cfg.circle_width**2))
    return -(ring * x.squeeze(1)).mean()


def schedules(t: int, cfg: UniverseConfig) -> tuple[float, float, float, float, float]:
    """Return alpha, beta, w_smooth, w_center, w_circle for step t."""
    s = t / max(cfg.T - 1, 1)
    alpha = cfg.alpha_max * s  # large early, smaller later
    beta = cfg.beta_max * s  # noise anneals to 0
    w_smooth = cfg.w_smooth_max * (s**0.5)
    w_center = cfg.w_center_max * (1 - s)
    w_circle = cfg.w_circle_max * (1 - s)
    return alpha, beta, w_smooth, w_center, w_circle


def energy_function(x: torch.Tensor, t: int, cfg: UniverseConfig, r_norm: torch.Tensor) -> torch.Tensor:
    alpha, beta, w_smooth, w_center, w_circle = schedules(t, cfg)
    del alpha, beta  # not used directly here
    E = (
        w_smooth * E_smooth(x)
        + w_center * E_center(x, r_norm)
        + w_circle * E_circle(x, r_norm, cfg)
    )
    return E


def compute_energy_gradient(
    x: torch.Tensor, t: int, cfg: UniverseConfig, r_norm: torch.Tensor
) -> torch.Tensor:
    x_var = x.clone().detach().requires_grad_(True)
    E = energy_function(x_var, t, cfg, r_norm)
    E.backward()
    return x_var.grad


def reverse_diffusion_step(
    x: torch.Tensor, t: int, cfg: UniverseConfig, r_norm: torch.Tensor
) -> torch.Tensor:
    grad = compute_energy_gradient(x, t, cfg, r_norm)
    alpha, beta, *_ = schedules(t, cfg)
    noise = torch.randn_like(x)
    x_new = x - alpha * grad + beta * noise
    return x_new.clamp(-3, 3).detach()


def save_image(x: torch.Tensor, path: str) -> None:
    img = x[0, 0].detach().cpu().numpy()
    img = (img - img.min()) / (img.max() - img.min() + 1e-8)
    plt.imsave(path, img, cmap="gray")


def run_universe_demo(cfg: UniverseConfig, out_dir: str = "demo/univ/outputs") -> None:
    os.makedirs(out_dir, exist_ok=True)
    set_seed(cfg.seed)
    x = init_state(cfg)
    r_norm = _radius_grid(cfg.image_size, cfg.image_size, cfg.device)

    for t in reversed(range(cfg.T)):
        x = reverse_diffusion_step(x, t, cfg, r_norm)
        if t % cfg.save_interval == 0 or t == 0:
            save_image(x, os.path.join(out_dir, f"step_{t:04d}.png"))

    save_image(x, os.path.join(out_dir, "final.png"))
    print(f"Saved samples to {out_dir}")


if __name__ == "__main__":
    cfg = UniverseConfig()
    run_universe_demo(cfg)
