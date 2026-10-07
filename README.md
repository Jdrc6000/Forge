# Forge (フォージ)
> A simple compiler written in Python.

![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Python](https://img.shields.io/badge/python-3.10+-blue.svg)

## Table of Contents
1. [About](#about)
2. [Pipeline Overview](#pipeline-overview)
3. [Features](#features)
4. [Notes](#notes)
5. [Roadmap](#roadmap)
6. [Examples](#examples)
7. [References](#references)

## About
Forge is an educational personal project designed to help understand how programming languages work under the hood.

## Pipeline Overview
1. Lexical Analysis - Converts source text into a stream of tokens.
2. Parser - Reads tokens and builds an Abstract Syntax Tree (AST).
3. Semantic Analysis - Checks types, scopes, and ensures valid constructs.
4. Optimisation (AST) - constant folding & dead-code elimination on the tree
5. IR Generation - register-based IR with backpatched jumps
6. CFG & Liveness - basic blocks, liveness analysis, unreachable-code & dead-store elimination
7. Register Allocation - linear scan with spilling to memory slots
8. Virtual Machine - dispatch loop, call frames, builtins, structs, modules

## Features
* Responsive error messages
* Custom builtin functions
* Optimisations: Dead Code Elimination (DCE), Constant Folding (CF)

## Notes
* This is just self-driven personal project, meaning:
    * The code will be messy
    * There will be bugs
    * It is not supposed to be easy to use
* In the latest commit, `main.py` is hardcoded to output many debug statements, thus this repo is not meant for beginners.
> 初心者向けではありません。デバッグ用出力が多く、コードも整理されていません。

## Roadmap
Planned improvements:
| Feature                          | Priority | Notes |
|----------------------------------|----------|-------|
| Additional optimisation passes   | low      |       |
| Real types instead of Python     | medium   | custom user types |
| Compile to bytecode              | low      | IR already ~90% there |
| String interpolation             | medium   | variables inside strings |
| Floor division                   | low      | add `//` |

## Examples
Below are some example code snippets that Forge can compile / run.
##### Functions, variables, and builtin functions
```
fn check(a, b) {
    if a == b {
        return "A is equal to B"
    } else {
        return "A is not equal to B"
    }
}

result = check(2, 5)
println(result)
```
###### Expected output:
```
A is not equal to B
```

##### While loops, continues + breaks, and builtin functions
```
i = 0
while i < 10 {
    i = i + 1
    if i == 3 { continue }
    if i == 7 { break }
    println(i)
}
```
###### Expected output:
```
1
2
4
5
6
```

##### The Collatz Conjecture
```
fn colltaz_conjecture(num) {
    if num % 2 == 0 {
        return int(num / 2)
    } else {
        return int(num * 3 + 1)
    }
}

curr_num = 5
index = 1
while curr_num != 1 {
    println("Step " + str(index) + ": " + str(curr_num))
    curr_num = colltaz_conjecture(curr_num)
    index = index + 1
}
println("Final step " + str(index) + ": " + str(curr_num))
```
###### Expected output:
```
Step 1: 5
Step 2: 16
Step 3: 8
Step 4: 4
Step 5: 2
Final step 6: 1
```

##### Chudnovsky algorithm (calculating digits of pi)
```
fn isqrt(n) {
    if n < 2 { return n }
    x = n
    y = (x + n // x) // 2
    while y < x {
        x = y
        y = (x + n // x) // 2
    }
    return x
}

fn chudnovsky(digits) {
    one = 10 ^ (2 * digits + 20)

    k = 1
    a_k = one
    a_sum = one
    b_sum = 0
    C = 640320
    C3_OVER_24 = C ^ 3 // 24
    while true {
        a_k = a_k * (-(6 * k - 5) * (2 * k - 1) * (6 * k - 1))
        a_k = a_k // (k * k * k * C3_OVER_24)
        a_sum = a_sum + a_k
        b_sum = b_sum + (k * a_k)
        k = k + 1
        if a_k == 0 { break }
    }
    total = 13591409 * a_sum + 545140134 * b_sum
    pi = (426880 * isqrt(10005 * one) * one) // total
    return pi // (10 ^ 20)
}

println(str(chudnovsky(25)))
```
###### Expected output:
```
3141592653589793
```

## References
- [Creating Your Own Programming Language with Dr Laurie Tratt - Computerphile](https://www.youtube.com/watch?v=Q2UDHY5as90)
- [Crafting Interpreters - Robert Nystrom](https://craftinginterpreters.com/contents.html)
- [Linear Scan Register Allocation - Massimiliano Poletto and Vivek Sarkar](https://web.cs.ucla.edu/~palsberg/course/cs132/linearscan.pdf)
- [Collatz conjecture - Lothar Collatz](https://en.wikipedia.org/wiki/Collatz_conjecture)
- [Chudnovsky algorithm - Chudnovsky brothers](https://en.wikipedia.org/wiki/Chudnovsky_algorithm)