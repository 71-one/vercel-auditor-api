"""
审核员代码库查询 API（Vercel 优化版）
- 数据按专业代码预先分组，查询时直接读取，避免遍历全表
- 只返回必要字段，减小响应体积
"""
import json
import os
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# ====== 启动时加载分组数据 ======
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "auditors_by_code.json")

with open(DATA_FILE, "r", encoding="utf-8") as f:
    AUDITORS_BY_CODE = json.load(f)

# 同时生成姓名索引（启动时一次性算好，避免每次请求遍历）
NAME_INDEX = {}
ALL_CODES = sorted(AUDITORS_BY_CODE.keys())
ALL_NAMES = set()
for code, auditors in AUDITORS_BY_CODE.items():
    for auditor in auditors:
        name = auditor["name"]
        ALL_NAMES.add(name)
        if name not in NAME_INDEX:
            NAME_INDEX[name] = {
                "systems": set(),
                "codes": set()
            }
        NAME_INDEX[name]["systems"].add(auditor.get("systems", ""))
        NAME_INDEX[name]["codes"].add(code)

ALL_NAMES = sorted(ALL_NAMES)


# ====== 接口1：根据专业代码查询审核员 ======
@app.route("/api/auditors", methods=["GET"])
def search_by_code():
    """
    精确查询某个专业代码下的所有审核员
    参数:
      - code: 专业代码（如 06.02.01）
      - system: 可选，体系筛选（如 Q / E / S / F）
    """
    code = request.args.get("code", "").strip()
    system = request.args.get("system", "").strip().upper()

    if not code:
        return jsonify({
            "success": False,
            "message": "请提供专业代码，例如: /api/auditors?code=06.02.01"
        }), 400

    auditors = AUDITORS_BY_CODE.get(code, [])

    # 可选：按体系筛选
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
    """查询某个审核员的所有专业代码"""
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
    """列出所有可用的专业代码"""
    return jsonify({
        "success": True,
        "total_codes": len(ALL_CODES),
        "codes": ALL_CODES
    })


# ====== 接口4：列出所有审核员 ======
@app.route("/api/names", methods=["GET"])
def list_names():
    """列出所有审核员姓名"""
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
        "endpoints": {
            "query_by_code": "/api/auditors?code=06.02.01",
            "query_by_name": "/api/auditor/付宏良",
            "all_codes": "/api/codes",
            "all_names": "/api/names"
        }
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=False)
