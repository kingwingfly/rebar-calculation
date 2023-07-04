from itertools import chain
from beam_rebar.run import Beams
from column_rebar.run import Columns
from plate_rebar.run import Plates
import os
import json
from pprint import pprint

SAVE_DIR = "total.json"
beam_datas = [
    os.path.join(os.path.dirname(__file__), "beam_rebar", f"structures-{i}")
    for i in ["1F", "2F", "3F", "top"]
]
plate_datas = [
    os.path.join(
        os.path.dirname(__file__), "plate_rebar", "structures", f"structures-{i}.json"
    )
    for i in ["1F", "2F"]
]
column_datas = [
    os.path.join(
        os.path.dirname(__file__), "column_rebar", "structures", f"structures.json"
    )
]

base_l = {
    32: 710160,
    28: 541900,
    25: 174362,
    22: 135836,
    18: 97208,
    16: 133516,
    14: 981088,
    12: 2504793,
    "箍筋12": 332674,
    "箍筋10": 834084,
    8: 2010305,
    "箍筋8": 1672862,
}


others_l = {
    25: 245412,  # 梁上柱纵筋
    20: 224544,  # AL纵筋
    14: 35781.6,  # TZ1纵筋
    12: 4588,  # 吊筋
    8: 146880  # 1F板上部贯通筋
    + 146880
    + 182160
    + 257040  # 2F板上部贯通筋
    + 212520
    + 18360
    + 18760
    + 60667.6  # TZ1箍筋
    + 1213844  # 檐口通长+分布筋
    + 119651  # AL箍筋
    + 374976,  # 梁上柱箍筋
    6: 2848300 + 2848300 + 3301200,  # 1F填充墙拉筋  # 2F填充墙拉筋  # 3F填充墙拉筋
}

density = {
    6: 0.222,
    8: 0.395,
    10: 0.617,
    12: 0.888,
    14: 1.21,
    16: 1.58,
    18: 2.0,
    20: 2.47,
    22: 2.98,
    25: 3.85,
    28: 4.83,
    30: 5.55,
    32: 6.31,
    "箍筋8": 0.395,
    "箍筋10": 0.617,
    "箍筋12": 0.888,
}

base_m = dict([(d, round(l / 1000 * density[d] / 1000, 3)) for d, l in base_l.items()])

others_m = dict(
    [(d, round(l / 1000 * density[d] / 1000, 3)) for d, l in others_l.items()]
)

if __name__ == "__main__":
    total_l = {}
    columns_l = {}
    beams_l = {}
    plates_l = {}
    details_l = {}
    columns_m = {}
    beams_m = {}
    plates_m = {}
    total_m = {}

    for path in column_datas:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            ret = Columns(data).run()
            for d, l in ret.items():
                columns_l[d] = columns_l.get(d, 0) + l
                columns_m[d] = columns_m.get(d, 0) + l / 1000 * density[d]
                total_l[d] = total_l.get(d, 0) + l
            details_l["柱"] = details_l.get("柱", {}) | {
                path.split("/")[-1].split(".")[0]: ret
            }

    for path in plate_datas:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            ret = Plates(data).run()
            for d, l in ret.items():
                plates_l[d] = columns_l.get(d, 0) + l
                plates_m[d] = plates_m.get(d, 0) + l / 1000 * density[d]
                total_l[d] = total_l.get(d, 0) + l
            details_l["板"] = details_l.get("板", {}) | {
                path.split("-")[-1].split(".")[0]: ret
            }

    for path in beam_datas:
        it = os.walk(path)
        for dirpath, dirnames, filenames in it:
            for file in filenames:
                with open(os.path.join(dirpath, file), "r", encoding="utf-8") as f:
                    data = json.load(f)
                    ret = Beams(data).run()
                    for d, l in ret.items():
                        beams_l[d] = beams_l.get(d, 0) + l
                        beams_m[d] = beams_m.get(d, 0) + l / 1000 * density[d]
                        total_l[d] = total_l.get(d, 0) + l
                    details_l["梁"] = details_l.get("梁", {}) | {
                        dirpath.split("-")[-1] + " " + file.split(".")[0]: ret
                    }
    for i in [columns_l, beams_l, plates_l, others_l, base_l, total_l]:
        for k in i.keys():
            i[k] = round(i[k] / 1000, 3)
        pprint(i)
    for d, l in chain(others_l.items(), base_l.items()):
        total_l[d] = total_l.get(d, 0) + l
    for d, l in total_l.items():
        total_m[d] = round(l * density[d], 3)
    for i in [columns_m, beams_m, plates_m, total_m]:
        for k in i.keys():
            i[k] = round(i[k] / 1000, 3)
        pprint(i)
    for i in details_l.keys():
        for j in details_l[i].keys():
            for k in details_l[i][j].keys():
                details_l[i][j][k] = round(details_l[i][j][k] / 1000, 3)
    pprint(details_l)
    with open(
        os.path.join(os.path.dirname(__file__), SAVE_DIR), "w", encoding="utf-8"
    ) as f:
        dic = dict(
            zip(
                [
                    "柱钢筋合计长度(m)",
                    "梁钢筋合计长度(m)",
                    "板钢筋合计长度(m)",
                    "基础钢筋合计长度(m)",
                    "其他手算部分合计长度(m)",
                    "全部钢筋合计长度(m)",
                    "柱钢筋合计质量(t)",
                    "梁钢筋合计质量(t)",
                    "板钢筋合计质量(t)",
                    "基础钢筋合计质量(t)",
                    "其他手算部分合计质量(t)",
                    "全部钢筋合计质量(t)",
                    "细节(m)",
                ],
                chain(
                    # map(
                    #     lambda d: dict(
                    #         sorted([(k, v) for k, v in d.items()], key=lambda x: -x[0])
                    #     ),
                    [
                        columns_l,
                        beams_l,
                        plates_l,
                        others_l,
                        base_l,
                        total_l,
                        columns_m,
                        beams_m,
                        plates_m,
                        base_m,
                        others_m,
                        total_m,
                    ],
                    # ),
                    [details_l],
                ),
            )
        )
        json.dump(dic, f, ensure_ascii=False)
