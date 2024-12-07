# SPDX-License-Identifier: MIT
# Copyright (c) 2024 Yingwei Zheng
# This file is licensed under the MIT License.
# Please refer to LICENSE for more information.

from layout import Circuit

n = 8
circuit = Circuit(left_margin=0)

first_idx = None
for i in range(n):
    idx = circuit.lstick(i, f'q_{i}')
    if first_idx is None:
        first_idx = idx
    else:
        circuit.align(first_idx, idx)

for i in range(n):
    circuit.H(i)
    for j in range(i + 1, n):
        circuit.control(j, i, f'R_{j - i + 1}')

for i in range(n // 2):
    circuit.SWAP(i, n - i - 1)

print(circuit)
