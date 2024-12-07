# SPDX-License-Identifier: MIT
# Copyright (c) 2024 Yingwei Zheng
# This file is licensed under the MIT License.
# Please refer to LICENSE for more information.

from layout import Circuit

circuit = Circuit()
circuit.control(1, 2, 'V')
circuit.CNOT(0, 1)
circuit.control(1, 2, R'V^\dagger')
circuit.CNOT(0, 1)
circuit.control(0, 2, 'V')

print(circuit)
