import json
from pprint import pprint
from .plate import UpperRebar, BottomRebar, Beam, Plate
import os


class Plates:
    def __init__(self, data) -> None:
        self.plates = [Plate(s) for s in data.get("plates", [])]
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
        for p in self.plates:
            ret[8] = ret.get(8, 0) + p.total_length
        for upper in self.uppers:
            ret[upper.d] = ret.get(upper.d, 0) + upper.total_length
        for bottom in self.bottoms:
            ret[bottom.d] = ret.get(bottom.d, 0) + bottom.total_length
        t = "直径\t总长度(m)\n"
        for d, l in ret.items():
            t += f"{d}\t{l/1000:.3f}\n"
        print(t)
        return ret


if __name__ == "__main__":
    filenames = ["structures-1F", "structures-2F"]
    for file in filenames:
        with open(
            os.path.join(os.path.dirname(__file__), f"structures/{file}.json"),
            "r",
            encoding="utf-8",
        ) as f:
            data = json.load(f)
            up = Plates(data)
            ret = up.run()
            pprint(ret)
