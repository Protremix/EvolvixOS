#!/usr/bin/env python3
"""ML Toolkit - scikit-learn (BSD) - 100% Free"""
import json, sys, subprocess


class Skill:
    def __init__(self, config: dict = None):
        self.config = config or {}

    def run(self, args: dict) -> dict:
        action = args.get("action", "classify")
        try:
            from sklearn import datasets, svm, cluster, decomposition
            from sklearn.model_selection import train_test_split
            from sklearn.metrics import accuracy_score
            import numpy as np
            if action == "classify":
                X = np.array(args.get("X", [])) if args.get("X") else datasets.load_iris().data
                y = np.array(args.get("y", [])) if args.get("y") else datasets.load_iris().target
                Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.3)
                clf = svm.SVC().fit(Xtr, ytr)
                return {"accuracy": float(accuracy_score(yte, clf.predict(Xte)))}
            elif action == "cluster":
                X = np.array(args.get("X", [])) if args.get("X") else datasets.load_iris().data
                km = cluster.KMeans(n_clusters=args.get("n_clusters",3), n_init=10).fit(X)
                return {"labels": km.labels_.tolist(), "centers": km.cluster_centers_.tolist()}
            elif action == "pca":
                X = np.array(args.get("X", [])) if args.get("X") else datasets.load_iris().data
                pca = decomposition.PCA(n_components=args.get("n_components",2)).fit(X)
                return {"reduced": pca.transform(X).tolist(), "variance": pca.explained_variance_ratio_.tolist()}
            return {"error": f"unknown: {action}"}
        except ImportError:
            subprocess.run([sys.executable, "-m", "pip", "install", "-q", "scikit-learn"], capture_output=True)
            return self.run(args)
        except Exception as e:
            return {"error": str(e)}


if __name__ == "__main__":
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(Skill().run(args)))
