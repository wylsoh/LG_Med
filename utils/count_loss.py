"""
Connected-component count supervision for segmentation.

Experiment goal: the number of connected components (infection regions) of the
predicted segmentation should match the quantity keyword from the text prompt
(e.g. "two" -> 2 regions).

  - soft_euler_count(prob): differentiable proxy of #foreground components via
    the Euler characteristic (chi = V - E + F, 4-connectivity). For solid
    (hole-free) blobs, chi == #components. Used as the training loss signal.
  - soft_euler_count(prob): differentiable proxy of #foreground components via
    the Euler characteristic (chi = V - E + F, 4-connectivity). For solid
    (hole-free) blobs, chi == #components. Used as the training loss signal.
  - count_components(mask): EXACT number of connected components (8-connectivity)
    via GPU label propagation (pure torch, no scipy). Used for evaluation.
"""

import torch
import torch.nn.functional as F


def soft_euler_count(prob: torch.Tensor) -> torch.Tensor:
    """Differentiable Euler characteristic proxy of #foreground components.

    For a binary image (4-connectivity): chi = V - E + F
        V = #foreground pixels
        E = #horizontal adjacencies + #vertical adjacencies
        F = #2x2 all-foreground blocks
    For solid (hole-free) blobs, chi == #components.

    `prob` is a soft (0-1) map, so chi is differentiable.

    Args:
        prob: (B, 1, H, W) probability map in [0, 1].
    Returns:
        (B,) soft Euler number (approx. component count).
    """
    p = prob[:, 0]  # (B, H, W)

    V = p.sum(dim=(1, 2))
    Eh = (p[:, :, :-1] * p[:, :, 1:]).sum(dim=(1, 2))
    Ev = (p[:, :-1, :] * p[:, 1:, :]).sum(dim=(1, 2))
    F = (p[:, :-1, :-1] * p[:, :-1, 1:] *
         p[:, 1:, :-1] * p[:, 1:, 1:]).sum(dim=(1, 2))

    return V - Eh - Ev + F  # (B,)


def _neighbors_min(t: torch.Tensor, sentinel: float,
                   connectivity: int = 8) -> torch.Tensor:
    """Min over the neighbors of each pixel (borders filled with sentinel).

    connectivity: 8 -> all 8 neighbors; 4 -> only orthogonal neighbors.
    """
    B, H, W = t.shape
    padded = F.pad(t.unsqueeze(1), (1, 1, 1, 1), value=sentinel).squeeze(1)
    if connectivity == 4:
        offsets = [(0, 1), (2, 1), (1, 0), (1, 2)]          # up/down/left/right
    else:
        offsets = [(0, 0), (0, 1), (0, 2), (1, 0), (1, 2),
                   (2, 0), (2, 1), (2, 2)]                  # all 8
    out = torch.full_like(t, sentinel)
    for dh, dw in offsets:
        out = torch.minimum(out, padded[:, dh:dh + H, dw:dw + W])
    return out


def count_components(mask: torch.Tensor, connectivity: int = 8,
                     max_iter: int = 512) -> torch.Tensor:
    """EXACT number of connected components of binary masks (pure torch, no scipy).

    Iterative label propagation: give every foreground pixel a unique id, then
    repeatedly replace each pixel's id by the min of its neighbors' ids until
    convergence. Background pixels are pinned to the sentinel so that separate
    foreground components can never connect through background. Each component
    then has a single (minimal) id, so the number of distinct foreground ids
    == number of connected components.

    Runs entirely on the input's device (GPU-friendly, batched).

    Args:
        mask: (B, H, W) boolean foreground mask.
        connectivity: 8 (default) or 4.
        max_iter: upper bound on propagation iterations.
    Returns:
        (B,) exact component counts.
    """
    B, H, W = mask.shape
    device = mask.device
    sentinel = float(H * W)
    ids = torch.arange(H * W, device=device).view(1, H, W).expand(B, H, W).clone()
    sentinel_t = torch.full_like(ids, sentinel)
    ids = torch.where(mask, ids, sentinel_t)

    for _ in range(max_iter):
        prev = ids
        ids = torch.minimum(ids, _neighbors_min(ids, sentinel, connectivity))
        ids = torch.where(mask, ids, sentinel_t)   # keep bg = sentinel (no leak)
        if torch.equal(ids, prev):
            break

    # count distinct ids among foreground pixels, per sample
    counts = torch.zeros(B, device=device)
    for b in range(B):
        fg_ids = ids[b][mask[b]]
        counts[b] = torch.unique(fg_ids).numel()
    return counts

