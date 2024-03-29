from .column import HoopRebar, LongRebar, Column
import json
from pprint import pprint
import os


class Columns:
    def __init__(self, data) -> None:
        self.cs = [
            Column(attri["a"], attri["b"], attri["d"], attri["hs"], attri["hls"], attri.get("num", 1))
            for attri in data["columns"].values()
        ]
        self.longs = [
            LongRebar(self.cs[i], attri["num"], attri["type"])
            for i, attris in enumerate(data["columns"].values())
            for attri in attris["rebars"].values()
        ]
        self.hoops = [
            HoopRebar(self.cs[i], attri["hoops"]["symbol"])
            for i, attri in enumerate(data["columns"].values())
        ]

    def run(self):
        ret = {}
        for l in self.longs:
            ret[l.d] = ret.get(l.d, 0) + l.total_length * l.c.num
        for h in self.hoops:
            ret[h.d] = ret.get(h.d, 0) + h.total_length * h.c.num
        t = "\n类型\t长度(m)\n"
        for d, l in ret.items():
            t += f"{d}\t{l/1000:.3f}\n"
        # print(t)
        return ret


if __name__ == "__main__":
    with open(
        os.path.join(os.path.dirname(__file__), "structures", "structures.json"),
        "r",
        encoding="utf-8",
    ) as f:
        data = json.load(f)
        s = Columns(data)
        ret = s.run()
        pprint(ret)
