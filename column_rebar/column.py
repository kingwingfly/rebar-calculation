import re

C = 20
MAO = 37
WAN = 15


class Column:
    def __init__(self, a: int, b: int, d: int, hs: list[int], hls: list[int], num: int) -> None:
        self.a = a
        self.b = b
        self.d = d
        self.hs = hs
        self.hls = hls
        self.num = num
        assert len(self.hls) - len(self.hs) == 1, "不合理数量的柱梁搭配"

    @property
    def hns(self):
        return [h - hl for h, hl in zip(self.hs, self.hls[1::])]


class HoopRebar:
    def __init__(
        self,
        c: Column,
        symbol: str,
    ) -> None:
        self.c = c
        pattern = re.compile(r"(\d+)@(\d+)/(\d+)")
        ret = re.match(pattern, symbol)
        assert ret, "底钢筋标识不合理"
        assert len(ret.groups()) == 3, "底钢筋标识不合理"
        # 直径 加密区间距 非加密区间距
        self.d, self.confined_space, self.sparse_space = map(int, ret.groups())
        self.ld = c.d

    @property
    def each_length(self):
        return (
            (self.c.a - 2 * C - self.d) * 4
            + (self.c.b - 2 * C - self.d) * 4
            + (
                (self.c.a - 2 * C - 2 * self.d - self.ld) / 3
                + self.ld
                + self.d
            )
            * 2
            + (
                (self.c.b - 2 * C - 2 * self.d - self.ld) / 3
                + self.ld
                + self.d
            )
            * 2
            + 1.9 * self.d * 6
            + max(10 * self.d, 75) * 6
        )

    @property
    def num(self):
        num = 0
        for n, hn in enumerate(self.c.hns):
            if n == 0:  # 基础顶到1F
                l = min(self.c.d * MAO, self.c.hs[0] - C)
                num += int(l / 500)
                l = max(500, hn / 6, self.c.a, self.c.b) * 2 + self.c.hls[1]
                num += int(l / self.confined_space)
                l = max(hn - max(500, hn / 6, self.c.a, self.c.b) * 2, 0)
                num += int(l / self.sparse_space)
                continue
            elif n == 1:  # 1F
                l = hn / 3 + max(500, hn / 6, self.c.a, self.c.b) + self.c.hls[n + 1]
                num += int(l / self.confined_space)
                l = hn - hn / 3 + max(500, hn / 6, self.c.a, self.c.b)
                assert l > 0
                num += int(l / self.sparse_space)
            elif n == len(self.c.hns) - 1:  # 顶
                l = max(500, hn / 6, self.c.a, self.c.b) * 2 + self.c.hls[n + 1]
                num += int(l / self.confined_space)
                l = hn - max(500, hn / 6, self.c.a, self.c.b) * 2
                assert l > 0
                num += int(l / self.sparse_space)
            else:  # 中间楼层
                l = max(500, hn / 6, self.c.a, self.c.b) * 2 + self.c.hls[n + 1]
                num += int(l / self.confined_space)
                l = hn - max(500, hn / 6, self.c.a, self.c.b) * 2
                assert l > 0
                num += int(l / self.sparse_space)
        return num

    @property
    def total_length(self):
        return self.num * self.each_length


class LongRebar:
    def __init__(self, c: Column, num: int, type: str) -> None:
        self.c = c
        self.d = c.d
        self.num = num
        self.type = type

    @property
    def each_length(self):
        l = sum(self.c.hs) - self.c.hls[-1]
        l += (
            MAO * self.d
            if MAO * self.d <= self.c.hls[0] - C  # 直锚
            else self.c.hls[0] - C + WAN * self.d
        )
        assert self.type in ["mid", "out", "inner"], f"unknown self.type{self.type}"
        if self.type == "mid":
            l += (
                MAO * self.d
                if MAO * self.d <= self.c.hls[-1] - C
                else 12 * self.d + self.c.hls[-1] - C
            )
        elif self.type == "out":
            l += MAO * self.d * 1.5 + 20 * self.d
        elif self.type == "inner":
            l += (
                MAO * self.d
                if MAO * self.d <= self.c.hls[-1] - C
                else 12 * self.d + self.c.hls[-1] - C
            )
        return l

    @property
    def total_length(self):
        return self.num * self.each_length


def test_hoop():
    c = Column(550, 550, 25, [750, 4200, 4200, 4200], [1250, 0, 600, 600, 900])
    h = HoopRebar(c, "8@100/200")
    print(h.num)
    print(h.each_length)
    print(h.total_length)


def test_long():
    c = Column(550, 550, 25, [750, 4200, 4200, 4200], [1250, 0, 600, 600, 900])
    l = LongRebar(c, 7, "out")
    print(l.num)
    print(l.each_length)
    print(l.total_length)


if __name__ == "__main__":
    test_hoop()
    test_long()
