"""
审核员代码库查询 API（Vercel 版）
- 读取 auditors.json，启动时自动构建分组索引
- 按专业代码精确查询
"""
import json
import os
from collections import defaultdict
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# ====== 启动时加载并构建索引 ======
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "auditors.json")

with open(DATA_FILE, "r", encoding="utf-8") as f:
    RAW_AUDITORS = json.load(f)

# 按专业代码分组
AUDITORS_BY_CODE = defaultdict(list)
NAME_INDEX = {}
ALL_NAMES = set()

for r in RAW_AUDITORS:
    code = r.get("专业代码", "")
    name = r.get("审核员姓名", "")
    if not code or not name:
        continue

    ALL_NAMES.add(name)

    if name not in NAME_INDEX:
        NAME_INDEX[name] = {
            "systems": set(),
            "codes": set()
        }
    NAME_INDEX[name]["systems"].add(r.get("具备体系", ""))
    NAME_INDEX[name]["codes"].add(code)

    existing = next((a for a in AUDITORS_BY_CODE[code] if a["name"] == name), None)
    if not existing:
        existing = {
            "name": name,
            "systems": r.get("具备体系", ""),
            "source": r.get("能力来源", ""),
            "certification_decision": r.get("认证决定", ""),
            "is_chief": r.get("首席", ""),
            "status": r.get("状态", ""),
            "responsible_systems": []
        }
        AUDITORS_BY_CODE[code].append(existing)

    existing["responsible_systems"].append({
        "system": r.get("体系", ""),
        "code": code,
        "name": r.get("专业名称", ""),
        "category_code": r.get("分类代码", "")
    })

# 排序
priority = {"学历+工作经历": 0, "同组扩展": 1}
for code in AUDITORS_BY_CODE:
    AUDITORS_BY_CODE[code].sort(key=lambda a: priority.get(a["source"], 2))

ALL_CODES = sorted(AUDITORS_BY_CODE.keys())
ALL_NAMES = sorted(ALL_NAMES)


# ====== 接口1：根据专业代码查询审核员 ======
@app.route("/api/auditors", methods=["GET"])
def search_by_code():
    code = request.args.get("code", "").strip()
    system = request.args.get("system", "").strip().upper()

    if not code:
        return jsonify({
            "success": False,
            "message": "请提供专业代码，例如: /api/auditors?code=06.02.01"
        }), 400

    auditors = AUDITORS_BY_CODE.get(code, [])

    if system:
        filtered = []
        for auditor in auditors:
            responsible = [r for r in auditor.get("responsible_systems", [])
                           if r.get("system", "").upper() == system]
            if responsible:
                new_auditor = dict(auditor)
                new_auditor["responsible_systems"] = responsible
                filtered.append(new_auditor)
        auditors = filtered

    return jsonify({
        "success": True,
        "query_code": code,
        "system_filter": system if system else "全部",
        "matched_auditor_count": len(auditors),
        "auditors": auditors
    })


# ====== 接口2：查询某个审核员的所有认证代码 ======
@app.route("/api/auditor/<name>", methods=["GET"])
def search_by_name(name):
    info = NAME_INDEX.get(name)
    if not info:
        return jsonify({
            "success": False,
            "message": f"未找到审核员: {name}"
        }), 404

    return jsonify({
        "success": True,
        "auditor": name,
        "systems": sorted(info["systems"]),
        "certified_code_count": len(info["codes"]),
        "code_list": sorted(info["codes"])
    })


# ====== 接口3：列出所有专业代码 ======
@app.route("/api/codes", methods=["GET"])
def list_codes():
    return jsonify({
        "success": True,
        "total_codes": len(ALL_CODES),
        "codes": ALL_CODES
    })


# ====== 接口4：列出所有审核员 ======
@app.route("/api/names", methods=["GET"])
def list_names():
    return jsonify({
        "success": True,
        "total_auditors": len(ALL_NAMES),
        "auditors": ALL_NAMES
    })


# ====== 健康检查 ======
@app.route("/", methods=["GET"])
def health():
    return jsonify({
        "service": "auditor-code-query-api",
        "status": "running",
        "total_codes": len(ALL_CODES),
        "total_auditors": len(ALL_NAMES),
        "endpoints": {
            "query_by_code": "/api/auditors?code=06.02.01",
            "query_by_name": "/api/auditor/付宏良",
            "all_codes": "/api/codes",
            "all_names": "/api/names"
        }
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=False)
