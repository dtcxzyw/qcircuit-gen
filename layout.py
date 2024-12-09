# SPDX-License-Identifier: MIT
# Copyright (c) 2024 Yingwei Zheng
# This file is licensed under the MIT License.
# Please refer to LICENSE for more information.

import z3
import abc

class Gate:
    def __init__(self, y, width, height):
        assert y >= 0 and width > 0 and height > 0
        self.y = y
        self.width = width
        self.height = height

    @abc.abstractmethod
    def draw(self, x, canvas):
        pass

class SingleBitGate(Gate):
    def __init__(self, y, name):
        super().__init__(y, 1, 1)
        self.name = name

    def draw(self, x, canvas):
        canvas[self.y][x] = self.name

class ControlGate(Gate):
    def __init__(self, src_bit, tgt_bit, name, invert):
        assert src_bit >= 0 and tgt_bit >= 0
        assert src_bit != tgt_bit
        super().__init__(min(src_bit, tgt_bit), 1, abs(src_bit - tgt_bit) + 1)
        self.src_bit = src_bit
        self.tgt_bit = tgt_bit
        self.name = name
        self.invert = invert

    def draw(self, x, canvas):
        inv = 'o' if self.invert else ''
        canvas[self.src_bit][x] = fr"\ctrl{inv}{{{self.tgt_bit - self.src_bit}}}"
        canvas[self.tgt_bit][x] = self.name

class SwapGate(Gate):
    def __init__(self, bit1, bit2):
        assert bit1 >= 0 and bit2 >= 0
        assert bit1 != bit2
        super().__init__(min(bit1, bit2), 1, abs(bit1 - bit2) + 1)
        self.bit1 = min(bit1, bit2)
        self.bit2 = max(bit1, bit2)

    def draw(self, x, canvas):
        canvas[self.bit1][x] = R"\qswap"
        for i in range(self.bit1 + 1, self.bit2):
            canvas[i][x] = R"\qw \qwx"
        canvas[self.bit2][x] = R"\qswap \qwx"

class Barrier(Gate):
    def __init__(self, src_bit, tgt_bit):
        assert src_bit >= 0 and tgt_bit >= 0
        assert src_bit != tgt_bit
        super().__init__(min(src_bit, tgt_bit), 1, abs(src_bit - tgt_bit) + 1)
        self.src_bit = min(src_bit, tgt_bit)
        self.tgt_bit = max(src_bit, tgt_bit)

    def draw(self, x, canvas):
        canvas[self.src_bit][x] = fr"\qw \barrier{{{self.tgt_bit - self.src_bit}}}"

class Circuit:
    def __init__(self, left_margin = 1, right_margin = 1):
        self.gates = []
        self.align_constraints = []
        self.left_margin = left_margin
        self.right_margin = right_margin

    def add_gate(self, gate):
        idx = len(self.gates)
        self.gates.append(gate)
        return idx
    
    def align(self, idx1, idx2):
        assert idx1 != idx2
        assert 0 <= idx1 < len(self.gates) and 0 <= idx2 < len(self.gates)
        self.align_constraints.append((idx1, idx2))
        
    def singlebit(self, tgt_bit, name):
        return self.add_gate(SingleBitGate(tgt_bit, fr"\gate{{{name}}}"))

    def control(self, src_bit, tgt_bit, name, invert = False):
        return self.add_gate(ControlGate(src_bit, tgt_bit, fr"\gate{{{name}}}", invert))

    def X(self, tgt_bit):
        return self.singlebit(tgt_bit, 'X')
    
    def Y(self, tgt_bit):
        return self.singlebit(tgt_bit, 'Y')

    def Z(self, tgt_bit):
        return self.singlebit(tgt_bit, 'Z')

    def H(self, tgt_bit):
        return self.singlebit(tgt_bit, 'H')

    def CNOT(self, src_bit, tgt_bit, invert = False):
        return self.add_gate(ControlGate(src_bit, tgt_bit, R"\targ", invert))

    def SWAP(self, bit1, bit2):
        return self.add_gate(SwapGate(bit1, bit2))
    
    def measure(self, tgt_bit):
        return self.add_gate(SingleBitGate(tgt_bit, R"\meter"))
    
    def lstick(self, tgt_bit, name):
        return self.add_gate(SingleBitGate(tgt_bit, fr'\lstick{{{name}}}'))
    
    def rstick(self, tgt_bit, name, classic = False):
        return self.add_gate(SingleBitGate(tgt_bit, fr'\rstick{{{name}}}' + (R'\cw' if classic else R'\qw')))

    def nbits(self, tgt_bit):
        return self.add_gate(SingleBitGate(tgt_bit, R"\qw{/^n}"))
    
    def barrier(self, src_bit, tgt_bit):
        return self.add_gate(Barrier(src_bit, tgt_bit))

    def __str__(self):
        s = z3.Optimize()
        vars = []
        max_x = sum(gate.width for gate in self.gates)
        max_y = max(gate.y + gate.height for gate in self.gates)
        pred = [ -1 ] * max_y
        for idx, gate in enumerate(self.gates):
            x = z3.Int(f"x{idx}")
            vars.append(x)
            s.add(x >= 0)
            s.add(x <= max_x)
            for i in range(gate.y, gate.y + gate.height):
                if pred[i] != -1:
                    s.add(vars[pred[i]] + self.gates[pred[i]].width <= x)
                pred[i] = idx

        for idx1, idx2 in self.align_constraints:
            s.add(vars[idx1] == vars[idx2])

        width = 0
        for idx in range(len(self.gates)):
            cur_width = vars[idx] + self.gates[idx].width
            width = z3.If(width < cur_width, cur_width, width)
        s.minimize(width)

        if s.check() != z3.sat:
            raise Exception("Unsatisfiable constraints")
        
        model = s.model()
        xs = []
        for idx in range(len(vars)):
            x = model[vars[idx]].as_long()
            xs.append(x)
        max_x = max(xs[idx] + self.gates[idx].width for idx in range(len(self.gates))) + self.left_margin + self.right_margin
        canvas = [[R'\qw' for _ in range(max_x)] for _ in range(max_y)]
        for idx, gate in enumerate(self.gates):
            x = xs[idx] + self.left_margin
            gate.draw(x, canvas)

        ret = R"""\begin{figure}[h]
\mbox{
\Qcircuit @C=.5em @R=0em @!R {
"""
        ret += '\\\\\n'.join('& ' + ' & '.join(row) for row in canvas)
        ret += R"""
}
}
\centering
\end{figure}
"""
        return ret
