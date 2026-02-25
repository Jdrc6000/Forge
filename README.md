# Forge (フォージ)
> A simple compiler written in Python.

![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Python](https://img.shields.io/badge/python-3.12+-blue.svg)

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
4. Intermediate Representation - Transforms the AST into a lower-level representation for optimisation.
5. Register Allocation - Assigns values to virtual registers effectively.
6. Virtual Machine - Executes the compiled code in a custom runtime environment.

## Features
* Responsive error messages
* Custom builtin functions
* Optimisations: Dead Code Elimination (DCE), Constant Folding (CF)
* Test suite (100 tests covering 8 classes)

## Notes
* This is just self-driven personal project, meaning:
    * The code will be messy
    * There will be bugs
    * It is not supposed to be easy to use
* In the latest commit, `main.py` is hardcoded to output many debug statements, thus this repo is not meant for beginners.
> 初心者向けではありません。デバッグ用出力が多く、コードも整理されていません。

## Roadmap
Planned improvements:
| Feature | Priority | Notes |
|---------|----------|-------|
| Additional optimisation passes | low |
| Hashmaps | high | map["key"] = value |
| Real types instead of Python types | medium | Support for custom types |
| Compile to bytecode | low |
| String interpolations | medium | Supports defining variables inside strings |

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

## References
- [Creating Your Own Programming Language with Dr Laurie Tratt - Computerphile](https://www.youtube.com/watch?v=Q2UDHY5as90)
- [Crafting Interpreters - Robert Nystrom](https://craftinginterpreters.com/contents.html)