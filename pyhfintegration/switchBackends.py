#!/usr/bin/env python3

import pyhf


# Switching backends
for _ in range(1000):
    pyhf.set_backend("tensorflow")
    pyhf.set_backend("jax")
