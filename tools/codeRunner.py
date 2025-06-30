import subprocess
import json

def CodeRunner(language, code):
    if language not in ["python", "javascript"]:
        raise ValueError("Unsupported language")
    print(language + ":\n" + code)
    code = code.replace("<br>", "\n")
    if language == "python":
        try:
            # 使用 subprocess 运行 Python 代码
            result = subprocess.run(
                ["python", "-c", code],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                return {"output": result.stdout}
            else:
                return {"error": result.stderr}
        except Exception as e:
            return {"error": str(e)}

    elif language == "javascript":
        try:
            # 使用 Node.js 运行 JavaScript 代码
            print("L27 before subprocess.run:" + code)
            result = subprocess.run(
                ["node", "-e", code],
                capture_output=True,
                text=True,
                timeout=10
            )
            print(result)
            if result.returncode == 0:
                print("L37 result.stdout=" + result.stdout)
                return {"output": result.stdout}
            else:
                return {"error": result.stderr}
        except Exception as e:
            return {"error": str(e)}
