import re

Types = [1, 2, 3, 4]

C = 20  # 保护层
WAN = 15  # 弯起的倍数
MAO = 37  # 锚固的倍数 如果非框架梁，则取12
OUTSET = 50  # 箍筋起始预留
CONFINED = 1.5  # 加密区倍数（梁高）
MAX = 9  # 每9米需要搭接


class Mode:
    KL = 1
    WKL = 2
    L = 3


MODE = Mode.KL


def switch_mode(mode: Mode):
    global C, WAN, MAO, OUTSET, CONFINED, MODE
    if mode == Mode.KL:
        MODE = Mode.KL
    elif mode == Mode.WKL:
        MODE = Mode.WKL
    elif mode == Mode.L:
        MODE = Mode.L


class Column:
    def __init__(self, b: int, edge=False) -> None:
        self.b = b
        self.edge = edge


class Beam:
    def __init__(self, l: int, c1: Column, c2: Column, b=None, h=None) -> None:
        self.l = l
        self.c1 = c1
        self.c2 = c2
        self.b = b
        self.h = h

    @property
    def true_length(self):
        return self.l - self.c1.b / 2 - self.c2.b / 2


class Rebar:
    def __init__(self, type_: int, d: int) -> None:
        self.type = type_
        self.d = d


# 通长筋
class LongRebar(Rebar):
    def __init__(
        self,
        type_: int,
        d: int,
        l: int,
        c1: Column,
        c2: Column,
        num: int,
        name=None,
        h1=None,
        h2=None,
    ) -> None:
        super().__init__(type_, d)
        self.l = l
        self.c1 = c1
        self.c2 = c2
        self.num = num
        self.name = name
        self.h1 = h1
        self.h2 = h2

    @property
    def each_length(self):
        l = MAO * self.d if self.name != "g" else WAN * self.d
        if l > self.c1.b - C and l > self.c2.b - C:
            if MODE == Mode.WKL and (self.name not in ["n", "g"]):
                assert self.h1 and self.h2, "屋面梁需要知道两端柱高以计算端支座锚固"
                return (
                    self.l + self.c1.b / 2 + self.c2.b / 2 - C * 4 + self.h1 + self.h2
                )
            return self.l + self.c1.b / 2 + self.c2.b / 2 - C * 2 + WAN * self.d * 2
        else:
            return self.l - self.c1.b / 2 - self.c2.b / 2 + l * 2

    @property
    def total_length(self):
        return self.each_length * self.num


# 负筋
class UpperRebar(Rebar):
    def __init__(
        self,
        type_: int,
        d: int,
        beam1: Beam | None,
        beam2: Beam | None,
        column: Column,
        position: int,
        num: int,
    ) -> None:
        super().__init__(type_, d)
        assert beam1 is not None or beam2 is not None, "不可同时为None"
        self.beam1 = beam1
        self.beam2 = beam2
        self.column = column
        self.position = position
        self.num = num

    @property
    def each_length(self):
        scale = 1 / 3 if self.position == 1 else 1 / 4
        if self.beam1 is None:
            if MODE == Mode.WKL:
                assert self.beam2.h, "屋面梁计算需要梁高"
                return (
                    self.beam2.true_length * scale
                    + self.column.b
                    + self.beam2.h
                    - 2 * C
                )
            return self.beam2.true_length * scale + self.column.b - C + WAN * self.d
        elif self.beam2 is None:
            if MODE == Mode.WKL:
                assert self.beam1.h, "屋面梁计算需要梁高"
                return (
                    self.beam1.true_length * scale
                    + self.column.b
                    + self.beam1.h
                    - 2 * C
                )
            return self.beam1.true_length * scale + self.column.b - C + WAN * self.d
        else:
            return (
                max(self.beam1.true_length, self.beam2.true_length) * scale * 2
                + self.column.b
            )

    @property
    def total_length(self):
        return self.num * self.each_length


# 下部钢筋
class DownRebar(Rebar):
    def __init__(
        self, type_: int, d: int, c1: Column, c2: Column, beam: Beam, num: int
    ) -> None:
        super().__init__(type_, d)
        self.c1 = c1
        self.c2 = c2
        self.beam = beam
        self.num = num

    @property
    def each_length(self):
        lae = max(MAO * self.d, 0.5 * self.beam.h + 5 * self.d)
        if self.beam.c1 == None or self.beam.c2 == None:
            raise NotImplemented("悬挑")
        ret = self.beam.true_length
        if MODE == Mode.L:
            l = 12 * self.d
            if self.c1.edge and l > self.c2.b - C:
                ret += self.c1.b - C + 6.9 * self.d
            else:
                ret += l
            if self.c2.edge and l > self.c2.b - C:
                ret += self.c2.b - C + 6.9 * self.d
            else:
                ret += l
            return ret
        assert MODE in [Mode.KL, Mode.WKL], "未知梁"
        if self.c1.edge and lae > self.c2.b - C:
            ret += self.c1.b - C + WAN * self.d
        else:
            ret += lae
        if self.c2.edge and lae > self.c2.b - C:
            ret += self.c2.b - C + WAN * self.d
        else:
            ret += lae
        return ret

    @property
    def total_length(self):
        return self.each_length * self.num


# 构造筋
class GRebar(Rebar):
    def __init__(self, type_: int, d: int, beam: Beam, num: int) -> None:
        super().__init__(type_, d)
        self.beam = beam
        self.num = num

    @property
    def each_length(self):
        return self.beam.true_length + 2 * WAN * self.d

    @property
    def total_length(self):
        return self.each_length * self.num


# 抗扭筋
class NRebar(Rebar):
    def __init__(self, type_: int, d: int, beam: Beam, num: int) -> None:
        super().__init__(type_, d)
        self.beam = beam
        self.num = num

    @property
    def each_length(self):
        # assert MAO * self.d < 475, "在本例中，抗扭筋无法直锚"
        return self.beam.true_length + 2 * MAO * self.d

    @property
    def total_length(self):
        return self.each_length * self.num


# 箍筋
class HoopBar:
    def __init__(
        self, beam: Beam, symbol: str, stirrup_d=None, inner_d=None, addition=0
    ) -> None:
        assert beam.b is not None, "箍筋计算需要知道梁宽"
        assert beam.h is not None, "箍筋计算需要知道梁高"

        pattern = re.compile(r"(\d+)@(\d+)(?:/(\d+))?\((\d+)\)")
        ret = re.match(pattern, symbol).groups()
        self.beam = beam
        self.d = int(ret[0])
        self.confined_space = int(ret[1])  # 加密区间距
        self.sparse_space = int(ret[2]) if ret[2] else None  # 稀疏区间距
        self.arm_num = int(ret[3])
        self.addition = addition
        if self.arm_num != 2:
            assert stirrup_d, f"{self.arm_num}肢箍需要知道角筋直径(stirrup_d)"
            assert inner_d, f"{self.arm_num}肢箍需要知道小箍筋所在纵筋直径(inner_d)"
            self.stirrup_d = stirrup_d
            self.inner_d = inner_d

    @property
    def num(self):
        confined = max(self.beam.h * CONFINED, 500)
        if self.sparse_space:
            assert self.beam.true_length - 2 * confined >= 0, "没有空间留给非加密区，图纸错误"
            return (
                2 * (int((confined - OUTSET) / self.confined_space) + 1)
                + (int((self.beam.true_length - 2 * confined) / self.sparse_space) - 1)
                + self.addition
            )
        else:
            return (
                int((self.beam.true_length - 2 * OUTSET) / self.confined_space)
                + 1
                + self.addition
            )

    @property
    def each_length(self):
        if self.arm_num == 2:
            return (
                (self.beam.b + self.beam.h - 4 * C - 2 * self.d) * 2
                + 1.9 * self.d * 2
                + max(10 * self.d, 75) * 2
            )
        elif self.arm_num == 4:
            return (
                (self.beam.h - 2 * C - self.d) * 4
                + (self.beam.b - 2 * C - self.d) * 2
                + (
                    (self.beam.b - 2 * C - 2 * self.d - self.stirrup_d) / 3
                    + self.inner_d
                    + self.d
                )
                * 2
                + 1.9 * self.d * 4
                + max(10 * self.d, 75) * 4
            )
        else:
            raise NotImplemented(f"{self.arm_num}肢箍还未实现计算长度")

    @property
    def total_length(self):
        return self.num * self.each_length


# 拉筋
class Tensile:
    def __init__(self, beam: Beam, space: int, num=2) -> None:
        assert beam.b is not None, "拉筋计算需要梁宽"
        self.d = 6 if beam.b <= 350 else 8
        self.beam = beam
        self.layer_num = num
        self.space = space

    @property
    def num(self):
        return (
            int((self.beam.true_length - 2 * OUTSET) / self.space) + 1
        ) * self.layer_num

    @property
    def each_length(self):
        return (
            self.beam.b - 2 * C - self.d + 2 * 1.9 * self.d + 2 * max(10 * self.d, 75)
        )

    @property
    def total_length(self):
        return self.each_length * self.num


def test_long():
    # KL1
    c1 = Column(550)
    c2 = Column(550)
    lr = LongRebar(2, 25, 13950, c1, c2, 2)
    exp = (13950 + 550 - C * 2 + WAN * 25 * 2) * 2
    assert lr.total_length == exp
    nr = LongRebar(2, 12, 13950, c1, c2, 4)
    exp = (13950 - 550 + MAO * 12 * 2) * 4
    assert nr.total_length == exp
    # L12
    switch_mode(Mode.L)
    c1 = Column(300)
    c2 = Column(300)
    lr = LongRebar(2, 20, 11000 + 100, c1, c2, 2)
    exp = (11100 + 300 - C * 2 + WAN * 20 * 2) * 2
    assert lr.total_length == exp
    # WKL5
    switch_mode(Mode.WKL)
    c1 = Column(500)
    c2 = Column(500)
    lr = LongRebar(2, 22, 28000, c1, c2, 2, h1=600, h2=600)
    exp = (28000 + 500 - C * 2 + 600 - C + 600 - C) * 2
    assert lr.total_length == exp
    switch_mode(Mode.KL)


def test_upper():
    # KL1
    c1 = Column(550)
    c2 = Column(500)
    c3 = Column(550)
    b2 = Beam(7975, c2, c3)
    ur = UpperRebar(3, 22, None, b2, c3, 1, 1)
    exp = ((7975 - 525) / 3 + 550 - C + WAN * 22) * 1
    assert abs(ur.total_length - exp) < 0.01
    b1 = Beam(5975, c1, c2)
    ur = UpperRebar(3, 22, b1, b2, c2, 2, 3)
    exp = ((7975 - 525) / 4 * 2 + 500) * 3
    assert ur.total_length == exp
    # L12
    switch_mode(Mode.L)
    c1 = Column(300)
    c2 = Column(300)
    c3 = Column(300)
    b1 = Beam(4000, c1, c2, h=500)
    b2 = Beam(7100, c2, c3, h=600)
    ur = UpperRebar(3, 20, None, b1, c1, 1, 1)
    exp = (4000 - 300) / 3 + 300 - C + WAN * 20
    assert ur.total_length == exp
    ur = UpperRebar(3, 20, b1, b2, c2, 1, 1)
    exp = (7100 - 300) / 3 * 2 + 300
    assert ur.total_length == exp
    # WKL5
    switch_mode(Mode.WKL)
    ur = UpperRebar(3, 20, b1, b2, c2, 1, 1)
    ...
    switch_mode(Mode.KL)


def test_down():
    c1 = Column(500, edge=True)
    c2 = Column(500)
    b = Beam(6000, c1, c2, h=500)
    dr = DownRebar(3, 22, c1, c2, b, 2)
    exp = (6000 + 250 - C + WAN * 22 - 250 + MAO * 22) * 2
    assert dr.total_length == exp


def test_G():
    c1 = Column(500)
    c2 = Column(500, edge=True)
    b = Beam(8000, c1, c2)
    gr = GRebar(3, 12, b, 4)
    exp = (8000 - 500 + 2 * WAN * 12) * 4
    assert gr.total_length == exp


def test_N():
    c1 = Column(500)
    c2 = Column(500, edge=True)
    b = Beam(8000, c1, c2)
    nr = NRebar(3, 12, b, 4)
    exp = (8000 - 500 + 2 * MAO * 12) * 4
    assert nr.total_length == exp


def test_hoop():
    c1 = Column(500)
    c2 = Column(500, edge=True)
    b = Beam(8000, c1, c2, b=350, h=650)
    s = "8@100(4)"
    hoopbar = HoopBar(b, s, stirrup_d=25, inner_d=25, addition=12)
    exp_l = (
        (650 - 2 * C - 8) * 4
        + (350 - 2 * C - 8) * 2
        + ((350 - 2 * C - 16 - 25) / 3 + 25 + 8) * 2
        + 11.9 * 8 * 4
    )
    exp_num = int((8000 - 500 - 100) / 100) + 1 + 12
    exp = exp_l * exp_num

    assert hoopbar.num == exp_num
    assert hoopbar.each_length == exp_l
    assert hoopbar.total_length == exp
    c1 = Column(500)
    c2 = Column(500, edge=True)
    b = Beam(6000, c1, c2, b=300, h=500)
    s = "10@100/150(2)"
    hoopbar = HoopBar(b, s, addition=6)
    exp_l = (500 - 2 * C - 10) * 2 + (300 - 2 * C - 10) * 2 + 11.9 * 10 * 2
    exp_num = (
        int((750 - 50) / 100)
        + 1
        + int((6000 - 500 - 750 * 2) / 150)
        - 1
        + int((750 - 50) / 100)
        + 1
        + 6
    )
    exp = exp_l * exp_num
    assert hoopbar.num == exp_num
    assert hoopbar.each_length == exp_l
    assert hoopbar.total_length == exp


def test_tensile():
    c1 = Column(500)
    c2 = Column(500, edge=True)
    b = Beam(8000, c1, c2, b=350)
    t = Tensile(b, 200, 2)
    exp_l = 350 - 2 * C - 6 + 2 * 1.9 * 6 + 2 * 75
    exp_n = (int((8000 - 500 - 100) / 200) + 1) * 2
    exp = exp_l * exp_n
    assert t.total_length == exp


if __name__ == "__main__":
    test_long()
    test_upper()
    test_down()
    test_G()
    test_N()
    test_hoop()
    test_tensile()
    print("test passed")
