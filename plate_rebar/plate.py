import re

MAO = 37
WAN = 15
C = 20
H = 100


class Plate:
    def __init__(self, s: str) -> None:
        self.a, self.b, self.l, self.r, self.t, self.d, self.n = tuple(
            map(int, s.split())
        )

    @property
    def total_length(self):
        # 负筋分布筋
        l1 = self.a - self.l - self.r + 300
        l2 = self.b - self.t - self.d + 300
        n1 = (self.b - self.t - self.d) // 200
        n2 = (self.a - self.l - self.r) // 200
        return (l1 * n1 + l2 * n2) * self.n


class Beam:
    def __init__(self, b: int, true_l: int = None, edge: bool = False) -> None:
        self.b = b
        self.edge = edge
        self.true_l = true_l


class BottomRebar:
    def __init__(self, symbol: str, b1: Beam, b2: Beam, l: int, range: int) -> None:
        pattern = re.compile(r"(\d+)@(\d+)")
        ret = re.match(pattern, symbol)
        assert ret, "底钢筋标识不合理"
        assert len(ret.groups()) == 2, "底钢筋标识不合理"
        self.d, self.space = map(int, ret.groups())
        self.b1, self.b2 = b1, b2
        self.true_l = l - self.b1.b / 2 - self.b2.b / 2
        self.range = range

    @property
    def each_length(self):
        assert self.b1.b and self.b2.b, "梁参数缺失"

        ret = self.true_l
        ret += max(5 * self.d, self.b1.b / 2) + max(5 * self.d, self.b2.b / 2)
        return ret

    @property
    def num(self):
        num = int((self.range - self.space) / self.space + 1)
        return num

    @property
    def total_length(self):
        return self.num * self.each_length


class UpperRebar:
    def __init__(
        self,
        symbol: str,
        b: Beam,
    ) -> None:
        pattern = re.compile(r"(\d+)@(\d+) (\d+) (\d+)")
        ret = re.match(pattern, symbol)
        assert ret, "负筋标识不合理"
        assert len(ret.groups()) == 4, "负筋标识不合理"
        self.d, self.space, self.l1, self.l2 = map(int, ret.groups())
        self.b = b

    @property
    def each_length(self):
        assert self.l1 or self.l2, "至少需要一侧的长度"
        ret = 0
        ret += self.l1 + self.l2
        if self.l1 and self.l2:
            ret += self.b.b + 2 * (H - C)
        else:
            la = MAO * self.d
            ret += H - C
            ret += la if la <= self.b.b - C else 0.6 * la + WAN * self.d
        return ret

    @property
    def num(self):
        return int(self.b.true_l / self.space)

    @property
    def total_length(self):
        # 负筋下的分布筋
        n1 = (self.l1 - self.space / 2) / self.space + 1 if self.l1 else 0
        n2 = (self.l2 - self.space / 2) / self.space + 1 if self.l2 else 0
        fengbu1 = (n1 + n2) * self.b.true_l
        return self.num * self.each_length + fengbu1


def test_bottom():
    b1 = Beam(300)
    b2 = Beam(300)
    br = BottomRebar("8@200", b1, b2, 3000, 3000)
    print(br.each_length)
    print(br.num)
    print(br.total_length)


def test_upper():
    b = Beam(300, 6000)
    ur = UpperRebar("8@200 2000 1500", b)
    print(ur.each_length)
    print(ur.num)
    print(ur.total_length)
    ur = UpperRebar("8@200 2000 0", b)
    print(ur.each_length)
    print(ur.num)
    print(ur.total_length)


if __name__ == "__main__":
    test_bottom()
    test_upper()
