"""
审核员代码库查询 API（Vercel 版）
- 根据专业代码精确查询审核员
- 根据审核员姓名查询其所有认证代码
- 列出所有可用专业代码
"""
import json
import os
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # 允许跨域访问（百炼平台需要）

# ====== 启动时加载数据 ======
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "auditors.json")

with open(DATA_FILE, "r", encoding="utf-8") as f:
    AUDITORS = json.load(f)


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

    # 精确匹配专业代码
    results = [r for r in AUDITORS if r.get("专业代码", "") == code]

    # 可选：按体系筛选
    if system:
        results = [r for r in results if r.get("体系", "").upper() == system]

    # 按审核员分组
    auditor_map = {}
    for r in results:
        name = r.get("审核员姓名", "")
        if name not in auditor_map:
            auditor_map[name] = {
                "name": name,
                "systems": r.get("具备体系", ""),
                "source": r.get("能力来源", ""),
                "certification_decision": r.get("认证决定", ""),
                "is_chief": r.get("首席", ""),
                "status": r.get("状态", ""),
                "responsible_systems": []
            }
        auditor_map[name]["responsible_systems"].append({
            "system": r.get("体系", ""),
            "code": r.get("专业代码", ""),
            "name": r.get("专业名称", ""),
            "category_code": r.get("分类代码", "")
        })

    auditor_list = list(auditor_map.values())

    return jsonify({
        "success": True,
        "query_code": code,
        "system_filter": system if system else "全部",
        "matched_auditor_count": len(auditor_list),
        "total_records": len(results),
        "auditors": auditor_list
    })


# ====== 接口2：查询某个审核员的所有认证代码 ======
@app.route("/api/auditor/<name>", methods=["GET"])
def search_by_name(name):
    """查询某个审核员的所有专业代码"""
    results = [r for r in AUDITORS if r.get("审核员姓名", "") == name]

    if not results:
        return jsonify({
            "success": False,
            "message": f"未找到审核员: {name}"
        }), 404

    codes = list(set(r.get("专业代码", "") for r in results))
    systems = list(set(r.get("具备体系", "") for r in results))

    return jsonify({
        "success": True,
        "auditor": name,
        "systems": systems,
        "certified_code_count": len(codes),
        "code_list": sorted(codes)
    })


# ====== 接口3：列出所有专业代码 ======
@app.route("/api/codes", methods=["GET"])
def list_codes():
    """列出所有可用的专业代码"""
    codes = sorted(set(r.get("专业代码", "") for r in AUDITORS))
    return jsonify({
        "success": True,
        "total_codes": len(codes),
        "codes": codes
    })


# ====== 接口4：列出所有审核员 ======
@app.route("/api/names", methods=["GET"])
def list_names():
    """列出所有审核员姓名"""
    names = sorted(set(r.get("审核员姓名", "") for r in AUDITORS))
    return jsonify({
        "success": True,
        "total_auditors": len(names),
        "auditors": names
    })


# ====== 健康检查 ======
@app.route("/", methods=["GET"])
def health():
    return jsonify({
        "service": "auditor-code-query-api",
        "status": "running",
        "total_records": len(AUDITORS),
        "endpoints": {
            "query_by_code": "/api/auditors?code=06.02.01",
            "query_by_name": "/api/auditor/付宏良",
            "all_codes": "/api/codes",
            "all_names": "/api/names"
        }
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=False)
