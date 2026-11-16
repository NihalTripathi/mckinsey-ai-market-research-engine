import json
import os

from services.charts import make_chart

# 1. one series
one = make_chart(["2024", "2025", "2026"], {"Market size": [1.2, 1.45, 5.76]},
                 "India EV market size by year", "Year", "USD billion", "market_size", job_id="job_test")

# 2. several estimates for the same years (disagreement shown side by side), with a gap
many = make_chart(["2025", "2026", "2030"],
                  {"IMARC": [1.45, None, None], "Markets and Markets": [None, 5.76, None],
                   "Expert Market Research": [7.38, None, 25.0], "Next MSC": [None, None, 1.65]},
                  "Estimates of the India EV market ($ billion)", "Year", "USD billion", "estimates", job_id="job_test")

# 3. company names with long labels
firms = make_chart(["Tata Power", "Indian Oil Corporation Limited", "BPCL", "HPCL"],
                   {"Public chargers": [7000, 18000, 6500, 5400]},
                   "Public chargers by operator", "Company", "Chargers", "operators", job_id="job_test")

for name, chart in (("one series", one), ("several estimates", many), ("operators", firms)):
    print(name, "->", chart["png_path"], "| plotly JSON ok:", bool(json.loads(chart["plotly_json"])["data"]))

# 4. nothing to draw
print("empty ->", make_chart([], {}, "t", "x", "y", "empty"))
print("all missing ->", make_chart(["a"], {"s": [None]}, "t", "x", "y", "empty"))
print("PNG files exist:", all(os.path.exists(c["png_path"]) for c in (one, many, firms)))