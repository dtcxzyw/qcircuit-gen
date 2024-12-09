# SPDX-License-Identifier: MIT
# Copyright (c) 2024 Yingwei Zheng
# This file is licensed under the MIT License.
# Please refer to LICENSE for more information.

from layout import Circuit

circuit = Circuit(left_margin=0, right_margin=0)
bit0 = circuit.lstick(0, R'\ket{0}')
bit1 = circuit.lstick(1, R'\ket{\psi}')
circuit.align(bit0, bit1)

circuit.H(0)
circuit.nbits(1)
# circuit.barrier(0, 1)

circuit.control(0, 1, R'U^{2^{k-1}}')
# circuit.barrier(0, 1)

circuit.singlebit(0, R'R_Z(\omega_k)')
# circuit.barrier(0, 1)

circuit.nbits(1)
circuit.H(0)
circuit.measure(0)
bit0 = circuit.rstick(0, R'x_k', classic=True)
bit1 = circuit.rstick(1, R'\ket{\psi}')
circuit.align(bit0, bit1)
print(circuit)
