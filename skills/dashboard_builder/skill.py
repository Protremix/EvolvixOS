#!/usr/bin/env python3
"""Dashboard Builder - Streamlit (Apache 2.0) - 100% Free"""
import json, sys, subprocess


class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}

    def run(self, args: dict) -> dict:
        action = args.get("action", "generate")
        try:
            if action == "generate":
                title = args.get("title", "EvolvixOS Dashboard")
                code_lines = [
                    "import streamlit as st",
                    "import pandas as pd",
                    'import plotly.express as px',
                    f'st.title("{title}")',
                    'file = st.file_uploader("Upload CSV", type=["csv"])',
                    "if file:",
                    "    df = pd.read_csv(file)",
                    "    st.dataframe(df)",
                    '    cols = df.select_dtypes(include="number").columns.tolist()',
                    "    if cols:",
                    '        x = st.selectbox("X", df.columns)',
                    '        y = st.selectbox("Y", cols)',
                    "        st.plotly_chart(px.bar(df, x=x, y=y))",
                ]
                out = args.get("output", "evolvix_dashboard.py")
                with open(out, "w") as f:
                    f.write("\n".join(code_lines))
                return {"file": out, "run": f"streamlit run {out}"}
            elif action == "run":
                port = args.get("port", 8501)
                path = args.get("file", "evolvix_dashboard.py")
                subprocess.Popen([sys.executable, "-m", "streamlit", "run", path, "--server.port", str(port)])
                return {"status": "running", "port": port, "url": f"http://localhost:{port}"}
            return {"error": f"unknown: {action}"}
        except Exception as e:
            return {"error": str(e)}


if __name__ == "__main__":
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
