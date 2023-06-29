import json
from pprint import pprint
from .beam import (
    LongRebar,
    UpperRebar,
    DownRebar,
    HoopBar,
    Tensile,
    GRebar,
    NRebar,
    Column,
    Beam,
    Mode,
    switch_mode,
)
import os


class Beams:
    def __init__(self, data) -> None:
        try:
            match data["mode"]:
                case "KL":
                    switch_mode(Mode.KL)
                case "WKL":
                    switch_mode(Mode.WKL)
                case "L":
                    switch_mode(Mode.L)
        except:
            raise IndexError("mode needed")
        self.num = data.get("num", 1)
        self.cs = [Column(attri["b"], attri["edge"]) for attri in data["cs"].values()]
        self.bs = [
            Beam(attri["l"], self.cs[i], self.cs[i + 1], attri["b"], attri["h"])
            for i, attri in enumerate(data["bs"].values())
        ]
        self.ls = [
            LongRebar(
                3,
                attri["d"],
                attri["l"],
                self.cs[0],
                self.cs[-1],
                attri["num"],
                name=name,
                h1=attri.get("h1", None),
                h2=attri.get("h2", None),
            )
            for name, attri in data["ls"].items()
        ]
        self.uppers = [
            UpperRebar(
                3,
                attri["d"],
                None if self.cs[i].edge and i == 0 else self.bs[i - 1],
                None if self.cs[i].edge and i != 0 else self.bs[i],
                self.cs[i],
                attri["position"],
                attri["num"],
            )
            for i, attris in enumerate(map(lambda x: x["uppers"], data["cs"].values()))
            for attri in attris.values()
        ]
        self.downs = [
            DownRebar(
                3, attri["d"], self.cs[i], self.cs[i + 1], self.bs[i], attri["num"]
            )
            for i, beam in enumerate(data["bs"].values())
            for attri in beam["downs"].values()
        ]
        self.hoops = [
            HoopBar(self.bs[i], **attri)
            for i, attri in enumerate(map(lambda x: x["hoop"], data["bs"].values()))
        ]
        self.tensiles = [
            Tensile(
                self.bs[i],
                space=attri["tensile"]["space"],
                num=attri["tensile"].get("num", 2),
            )
            for i, attri in enumerate(data["bs"].values())
            if attri["tensile"]
        ]
        self.gs = [
            GRebar(3, attri["d"], self.bs[i], attri["num"])
            for i, attri in enumerate(map(lambda x: x["G"], data["bs"].values()))
            if attri
        ]
        self.ns = [
            NRebar(3, attri["d"], self.bs[i], attri["num"])
            for i, attri in enumerate(map(lambda x: x["N"], data["bs"].values()))
            if attri
        ]

    def run(self):
        from itertools import chain

        ret = ""
        # ret += f"种类\t直径\t数量\t单长\t总长\n"

        total_dic = {}
        for ty, beams in zip(
            ["通长", "上部", "下部", "构造", "抗扭", "箍", "拉"],
            [
                self.ls,
                self.uppers,
                self.downs,
                self.gs,
                self.ns,
                self.hoops,
                self.tensiles,
            ],
        ):
            for beam in beams:
                # ret += f"{ty}筋\t{beam.d}\t{beam.num}\t{beam.each_length:.0f}\t{beam.total_length:.0f}\n"
                total_dic[beam.d] = (
                    total_dic.get(beam.d, 0) + beam.total_length * self.num
                )
        ret += f"\n直径\t总长度(m)\n"
        total_dic = dict(sorted(list(total_dic.items()), key=lambda x: -int(x[0])))
        for d, l in total_dic.items():
            ret += f"{d}\t{l/1000:.3f}\n"
        # print(ret)
        return total_dic


if __name__ == "__main__":
    structures = ["structures-1F", "structures-2F", "structures-3F", "structures-top"]
    for struct in structures:
        it = os.walk(os.path.join(os.path.dirname(__file__), struct))
        for dirpath, dirnames, filenames in it:
            for file in filenames:
                with open(os.path.join(dirpath, file), "r", encoding="utf-8") as f:
                    data = json.load(f)
                bs = Beams(data)
                ret = bs.run()
                print(ret, end=",")
                # with open(
                #     os.path.join(
                #         os.path.dirname(__file__),
                #         "output",
                #         file.removesuffix(".json") + ".txt",
                #     ),
                #     "w",
                #     encoding="utf-8",
                # ) as f:
                #     f.write(ret)
