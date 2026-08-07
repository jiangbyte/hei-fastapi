import ast
import re
from pathlib import Path

ROOT = Path("app/modules")
SKIP_HEADER = ("由 HEI 代码生成器生成", "生成时间：", "Author: Charlie")


def is_english_text(s: str) -> bool:
    s = s.strip()
    if not s or len(s) < 3:
        return False
    if re.search(r"[A-Za-z]{3,}", s):
        ascii_words = re.findall(r"[A-Za-z]+", s)
        chinese = re.findall(r"[\u4e00-\u9fff]", s)
        if len(chinese) >= max(1, len("".join(ascii_words)) // 2):
            return False
        return True
    return False


results = []
for fp in sorted(ROOT.rglob("*.py")):
    text = fp.read_text(encoding="utf-8")
    lines = text.splitlines()
    try:
        tree = ast.parse(text)
        if (
            tree.body
            and isinstance(tree.body[0], ast.Expr)
            and isinstance(tree.body[0].value, ast.Constant)
            and isinstance(tree.body[0].value.value, str)
        ):
            ds = tree.body[0].value.value.strip()
            if is_english_text(ds) and not any(x in ds for x in SKIP_HEADER):
                results.append((str(fp), 1, "module_doc", ds[:100]))
    except SyntaxError:
        pass

    for node in ast.walk(ast.parse(text)):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            doc = ast.get_docstring(node)
            if doc and is_english_text(doc):
                results.append((str(fp), node.lineno, "docstring", doc.replace("\n", " ")[:120]))

    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("#"):
            comment = stripped[1:].strip()
            if is_english_text(comment):
                results.append((str(fp), i, "comment", comment[:120]))

out = Path("_comment_scan_out.txt")
lines_out = [f"Total items: {len(results)}"]
for r in results:
    lines_out.append(f"{r[1]:4d} {r[2]:12s} {r[0]} | {r[3]}")
out.write_text("\n".join(lines_out), encoding="utf-8")
print(f"Wrote {len(results)} items to {out}")
