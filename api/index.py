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
                "姓名": name,
                "具备体系": r.get("具备体系", ""),
                "能力来源": r.get("能力来源", ""),
                "认证决定": r.get("认证决定", ""),
                "首席": r.get("首席", ""),
                "状态": r.get("状态", ""),
                "负责体系": []
            }
        auditor_map[name]["负责体系"].append({
            "体系": r.get("体系", ""),
            "专业代码": r.get("专业代码", ""),
            "专业名称": r.get("专业名称", ""),
            "分类代码": r.get("分类代码", "")
        })

    auditor_list = list(auditor_map.values())

    return jsonify({
        "success": True,
        "查询代码": code,
        "体系筛选": system if system else "全部",
        "匹配审核员数": len(auditor_list),
        "总记录数": len(results),
        "审核员列表": auditor_list
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
        "审核员": name,
        "具备体系": systems,
        "认证专业代码数": len(codes),
        "专业代码列表": sorted(codes)
    })


# ====== 接口3：列出所有专业代码 ======
@app.route("/api/codes", methods=["GET"])
def list_codes():
    """列出所有可用的专业代码"""
    codes = sorted(set(r.get("专业代码", "") for r in AUDITORS))
    return jsonify({
        "success": True,
        "专业代码总数": len(codes),
        "专业代码列表": codes
    })


# ====== 接口4：列出所有审核员 ======
@app.route("/api/names", methods=["GET"])
def list_names():
    """列出所有审核员姓名"""
    names = sorted(set(r.get("审核员姓名", "") for r in AUDITORS))
    return jsonify({
        "success": True,
        "审核员总数": len(names),
        "审核员列表": names
    })


# ====== 健康检查 ======
@app.route("/", methods=["GET"])
def health():
    return jsonify({
        "service": "审核员代码库查询API",
        "status": "running",
        "总记录数": len(AUDITORS),
        "接口列表": {
            "查询专业代码": "/api/auditors?code=06.02.01",
            "查询审核员": "/api/auditor/付宏良",
            "所有代码": "/api/codes",
            "所有审核员": "/api/names"
        }
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=False)
