"""Ekologická inference – Goodmanova regrese s omezeními (jen numpy).

Y ≈ X · B, kde řádky X a Y jsou složení jednotek (okrsků) a B je matice přesunů
s řádky na simplexu (každý řádek ≥ 0 a součet 1). Řeší se projekcí gradientu.
Bootstrap používá stejný počet iterací jako hlavní odhad, aby intervaly odpovídaly bodovému odhadu.
"""
import numpy as np

ITERS = 6000


def proj_rows(V):
    """Projekce každého řádku matice na pravděpodobnostní simplex."""
    n = V.shape[1]
    U = -np.sort(-V, axis=1)
    css = np.cumsum(U, axis=1) - 1
    cond = U * np.arange(1, n + 1) > css
    rho = n - 1 - np.argmax(cond[:, ::-1], axis=1)
    theta = css[np.arange(len(V)), rho] / (rho + 1)
    return np.maximum(V - theta[:, None], 0)


def fit(X, Y, w, iters=ITERS):
    X, Y = np.asarray(X, float), np.asarray(Y, float)
    W = np.sqrt(np.asarray(w, float) / np.mean(w))[:, None]
    Xw, Yw = X * W, Y * W
    B = np.tile(Y.mean(0), (X.shape[1], 1))
    step = 1 / np.linalg.norm(Xw.T @ Xw, 2)
    for _ in range(iters):
        B = proj_rows(B - step * (Xw.T @ (Xw @ B - Yw)))
    return B


def bootstrap(X, Y, w, rng, n=200, iters=ITERS):
    X, Y, w = np.asarray(X, float), np.asarray(Y, float), np.asarray(w, float)
    out = []
    for _ in range(n):
        ix = rng.integers(0, len(X), len(X))
        out.append(fit(X[ix], Y[ix], w[ix], iters=iters))
    return np.array(out)
