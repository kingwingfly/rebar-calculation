import json
from pprint import pprint
from plate import UpperRebar, BottomRebar, Beam


class Uppers:
    def __init__(self, data) -> None:
        self.uppers = [
            UpperRebar(attri["symbol"], b=Beam(attri["b"], true_l=attri["true_l"]))
            for attri in data.get("uppers", [])
            for _ in range(attri.get("num", 1))
        ]
        self.bottoms = [
            BottomRebar(
                attri["symbol"],
                b1=Beam(attri["b1"]),
                b2=Beam(attri["b2"]),
                l=attri["l"],
                range=attri["range"],
            )
            for attri in data.get("bottoms", [])
            for _ in range(attri.get("num", 1))
        ]

    def run(self):
        ret = {}
        for upper in self.uppers:
            ret[upper.d] = ret.get(upper.d, 0) + upper.total_length
        for bottom in self.bottoms:
            ret[bottom.d] = ret.get(bottom.d, 0) + bottom.total_length
        t = "直径\t总长度\n"
        for d, l in ret.items():
            t += f"{d}\t{l/1000:.3f}\n"
        print(t)
        return t


if __name__ == "__main__":
    filenames = ["structures-1F", "structures-2F"]
    for file in filenames:
        with open(f"./structures/{file}.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            up = Uppers(data)
            up.run()
