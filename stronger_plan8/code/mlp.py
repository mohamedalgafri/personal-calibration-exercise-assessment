"""Numpy MLP ensemble for PLAN8 (stronger general model). Same interface idea as LogReg: fit / pred / predict_proba,
class-balanced sample weights, keep_scaler and warm start (init) for adaptation.
Architecture fixed in PLAN8: 2 hidden layers (128, 64), ReLU, softmax output, Adam, L2 weight decay, mini-batches."""
import numpy as np


def softmax(Z):
    Z = Z - Z.max(1, keepdims=True); E = np.exp(Z); return E / E.sum(1, keepdims=True)


def class_balance(y, w, C):
    w = w.astype(float).copy(); tot = w.sum()
    for c in range(C):
        s = w[y == c].sum()
        if s > 0:
            w[y == c] *= tot / (C * s)
    return w


class MLP:
    def __init__(self, C, hidden=(128, 64), l2=1e-4, lr=1e-3, epochs=60, batch=256, seed=0):
        self.C, self.hidden, self.l2, self.lr, self.epochs, self.batch, self.seed = C, hidden, l2, lr, epochs, batch, seed

    def _init(self, d):
        rng = np.random.default_rng(self.seed); sizes = [d, *self.hidden, self.C]
        self.P = []
        for a, b in zip(sizes[:-1], sizes[1:]):
            self.P += [rng.normal(0, np.sqrt(2.0 / a), (a, b)), np.zeros(b)]

    def _forward(self, Z):
        acts = [Z]; h = Z
        for i in range(0, len(self.P) - 2, 2):
            h = np.maximum(h @ self.P[i] + self.P[i + 1], 0); acts.append(h)
        return acts, h @ self.P[-2] + self.P[-1]

    def fit(self, X, y, w=None, init=None, keep_scaler=False, steps=None):
        if not keep_scaler:
            self.mu = X.mean(0); self.sd = X.std(0); self.sd[self.sd < 1e-9] = 1.0
        Z = (X - self.mu) / self.sd; n = len(Z); Y = np.eye(self.C)[y]
        w = class_balance(y, np.ones(n) if w is None else w, self.C)
        w = w / w.mean()
        if init is None:
            self._init(Z.shape[1])
        else:
            self.P = [p.copy() for p in init]
        m = [np.zeros_like(p) for p in self.P]; v = [np.zeros_like(p) for p in self.P]
        rng = np.random.default_rng(self.seed + 1000); t = 0
        total = steps if steps is not None else self.epochs * max(1, int(np.ceil(n / self.batch)))
        while t < total:
            order = rng.permutation(n)
            for s in range(0, n, self.batch):
                if t >= total:
                    break
                idx = order[s:s + self.batch]; t += 1
                acts, out = self._forward(Z[idx])
                G = (softmax(out) - Y[idx]) * w[idx, None] / len(idx)
                grads = [None] * len(self.P)
                grads[-2] = acts[-1].T @ G + self.l2 * self.P[-2]; grads[-1] = G.sum(0)
                d = G @ self.P[-2].T
                for i in range(len(self.P) - 4, -1, -2):
                    d = d * (acts[i // 2 + 1] > 0)
                    grads[i] = acts[i // 2].T @ d + self.l2 * self.P[i]; grads[i + 1] = d.sum(0)
                    if i > 0:
                        d = d @ self.P[i].T
                for k, gk in enumerate(grads):
                    m[k] = .9 * m[k] + .1 * gk; v[k] = .999 * v[k] + .001 * gk ** 2
                    self.P[k] -= self.lr * (m[k] / (1 - .9 ** t)) / (np.sqrt(v[k] / (1 - .999 ** t)) + 1e-8)
        return self

    def proba(self, X):
        return softmax(self._forward((X - self.mu) / self.sd)[1])


class Ensemble:
    """Average of K MLPs with different seeds (PLAN8: K = 3)."""
    def __init__(self, C, K=3, **kw):
        self.C, self.K, self.kw = C, K, kw

    def fit(self, X, y, w=None):
        self.members = [MLP(self.C, seed=k, **self.kw).fit(X, y, w) for k in range(self.K)]
        self.mu, self.sd = self.members[0].mu, self.members[0].sd
        return self

    def adapt(self, X, y, w, steps=60, lr=5e-4):
        """warm-start fine-tuning of every member, keeping each member's scaler (PLAN8 §4)."""
        new = Ensemble(self.C, self.K, **self.kw); new.members = []
        for m0 in self.members:
            m = MLP(self.C, seed=m0.seed, **{**self.kw, 'lr': lr}); m.mu, m.sd = m0.mu, m0.sd
            new.members.append(m.fit(X, y, w, init=m0.P, keep_scaler=True, steps=steps))
        return new

    def pred(self, X):
        return np.mean([m.proba(X) for m in self.members], 0).argmax(1)
