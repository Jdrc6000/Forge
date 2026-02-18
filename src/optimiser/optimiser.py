from src.optimiser.passes import ConstantFolder, DeadCodeEliminator

class Optimiser:
    def __init__(self):
        self.passes = [
            ConstantFolder(),
            DeadCodeEliminator(),
        ]

    def optimise(self, tree):
        for p in self.passes:
            tree = p.run(tree)
        return tree