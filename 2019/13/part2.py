#!/usr/local/bin/python3

import collections
import os

IN = 1
OUT = 2

with open("input.txt") as f:
    program = [int(word) for word in f.readline().split(",")]

class VM(object):
    def __init__(self, program, input=None):
        self.program = collections.defaultdict(int)
        for i, instruction in enumerate(program.copy()):
            self.program[i] = instruction
        self.input = input
        self.outputs = []
        self.pc = 0
        self.relative_base = 0
        self.halted = False

        self.instruction_defs = {}
        def add_instruction(op_code, param_types, impl, autoincrement_pc=True):
            self.instruction_defs[op_code] = [param_types, impl, autoincrement_pc]

        add_instruction(1, [IN, IN, OUT], lambda a, b: a + b) # add
        add_instruction(2, [IN, IN, OUT], lambda a, b: a * b) # multiply
        add_instruction(3, [OUT], lambda: self.input) # read input
        add_instruction(4, [IN], lambda a: self.outputs.append(a)) # output value
        add_instruction(5, [IN, IN], self.jump_if_true, autoincrement_pc=False)  # jump-if-true
        add_instruction(6, [IN, IN], self.jump_if_false, autoincrement_pc=False) # jump-if-false
        add_instruction(7, [IN, IN, OUT], lambda a, b: 1 if a < b else 0)  # less than
        add_instruction(8, [IN, IN, OUT], lambda a, b: 1 if a == b else 0)  # equals
        add_instruction(9, [IN], self.set_relative_base)  # adjust the relative base
        add_instruction(99, [], self.halt) # halt

    def run(self):
        while not self.halted:
            self.step()

    def run_until_output(self):
        initial_output_len = len(self.outputs)
        while len(self.outputs) == initial_output_len:
            self.step()
            if self.halted:
                break
        return self.outputs[-1]

    def step(self):
        instruction = self.program[self.pc]
        op_code = instruction % 100
        mode1 = int(instruction/100) % 10
        mode2 = int(instruction/1000) % 10
        mode3 = int(instruction/10000) % 10
        def apply_in_mode(param, mode):
            if mode == 0:
                return self.program[param]
            elif mode == 1:
                return param
            elif mode == 2:
                return self.program[param + self.relative_base]
            else:
                raise Exception("Unexpected in mode %d", mode)

        def apply_out_mode(param, mode):
            if mode == 0:
                return param
            elif mode == 2:
                return param + self.relative_base
            else:
                raise Exception("Unexpected out mode %d", mode)

        if op_code not in self.instruction_defs:
            raise Exception("Unexpected op code %d", op_code)

        param_types, impl, autoincrement_pc = self.instruction_defs[op_code]
        # TODO: generify if we end up with many parameter types
        if param_types == [IN, IN, OUT]:
            in1 = apply_in_mode(self.program[self.pc + 1], mode1)
            in2 = apply_in_mode(self.program[self.pc + 2], mode2)
            out = apply_out_mode(self.program[self.pc + 3], mode3)
            self.program[out] = impl(in1, in2)
        elif param_types == [IN, IN]:
            in1 = apply_in_mode(self.program[self.pc + 1], mode1)
            in2 = apply_in_mode(self.program[self.pc + 2], mode2)
            impl(in1, in2)
        elif param_types == [IN]:
            in1 = apply_in_mode(self.program[self.pc + 1], mode1)
            impl(in1)
        elif param_types == [OUT]:
            out = apply_out_mode(self.program[self.pc + 1], mode1)
            self.program[out] = impl()
        elif param_types == []:
            impl()
        else:
            raise Exception("Unexpected parameter types %s", param_types)

        if autoincrement_pc:
            self.pc += len(param_types) + 1

    def jump_if_true(self, a, b):
        if a != 0:
            self.pc = b
        else:
            self.pc += 3

    def jump_if_false(self, a, b):
        if a == 0:
            self.pc = b
        else:
            self.pc += 3

    def set_relative_base(self, a):
        self.relative_base += a

    def halt(self):
        self.halted = True

class Screen:
    def __init__(self):
        self.max_x = None
        self.max_y = None
        self.tiles = collections.defaultdict(int)
        self.seen_blocks = False
        self.block_count = 0
        self.score = 0

    def set_tile(self, x, y, tile):
        if self.max_x is None or x > self.max_x:
            self.max_x = x
        if self.max_y is None or y > self.max_y:
            self.max_y = y
        was_block = self.tiles[self.key(x, y)] == 2
        self.tiles[self.key(x, y)] = tile
        if tile == 2 and not was_block:
            self.block_count += 1
        elif tile != 2 and was_block:
            self.block_count -= 1
        if tile == 2:
            self.seen_blocks = True

    def key(self, x, y):
        return f"{x}-{y}"

    def print(self):
        os.system("clear")
        for y in range(self.max_y):
            line = ""
            for x in range(self.max_x):
                tile = self.tiles[self.key(x, y)]
                if tile == 0: # empty
                    line += " "
                elif tile == 1: # wall
                    line += "|"
                elif tile == 2: # block
                    line += "="
                elif tile == 3: # paddle
                    line += "-"
                elif tile == 4:
                    line += "o"
                else:
                    raise Error("Unexpected tile: %d" % tile)
            print(line)
        print("Score: %d Blocks remaining: %d" % (self.score, self.block_count))

program[0] = 2
vm = VM(program)
vm.input = 0
screen = Screen()
ball_x = None
paddle_x = None
while not vm.halted:
    x = vm.run_until_output()
    y = vm.run_until_output()
    tile = vm.run_until_output()
    if x == -1 and y == 0:
        screen.score = tile
        screen.print()
        if screen.seen_blocks and screen.block_count == 0:
            break
        continue
    screen.set_tile(x, y, tile)
    if tile == 3:
        paddle_x = x
    elif tile == 4:
        ball_x = x
    if ball_x is not None and paddle_x is not None:
        if ball_x > paddle_x:
            vm.input = 1
        elif ball_x < paddle_x:
            vm.input = -1
        else:
            vm.input = 0
