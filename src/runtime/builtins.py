class Builtins:
    @staticmethod
    def print(vm, args_regs):
        values = [vm.regs[r.id] for r in args_regs]
        print(*values, sep=" ", end="\n")

BUILTIN_FUNCTIONS = {
    "print": Builtins.print
}