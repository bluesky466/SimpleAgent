import os
import re
import subprocess

class SkillLoader:
    def __init__(self, skill_dir: str):
        self._skill_dir = skill_dir

    def _load_skills(self):
        skills = []
        for file in os.listdir(self._skill_dir):
            skill_path = os.path.join(self._skill_dir, file, "SKILL.md")
            if not os.path.exists(skill_path):
                continue
            with open(skill_path, "r") as f:
                content = f.read()
                metadata = self._get_skill_metadata(content)
                metadata["location"] = skill_path
                skills.append(metadata)
        return skills
    
    def get_skills_prompt(self):
        prompt = "下面是你的SKILLS列表,在需要的时候向用户请求加载skill权限通过后读取对应SKILL的完整描述并执行. \n"
        prompt += "<skills>\n"
        for skill in self._load_skills():
            prompt += f"    <skill>\n"
            prompt += f"        <name>{skill['name']}</name>\n"
            prompt += f"        <description>{skill['description']}</description>\n"
            prompt += f"        <location>{skill['location']}</location>\n"
            prompt += f"    </skill>\n"
        prompt += "</skills>\n"
        return prompt

    def _get_skill_metadata(self, content: str) -> dict | None:
        if not content.startswith("---"):
            return None
        match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
        if not match:
            return None
        metadata = {}
        for line in match.group(1).split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                metadata[key.strip()] = value.strip().strip('"\'')
        return metadata
    
    def exec_skill_py_script(self, script_path: str, arguments: list[str]):
        abs_script_path = os.path.abspath(os.path.expanduser(script_path))
        if not os.path.isfile(abs_script_path):
            return f"执行脚本失败，找不到文件: {abs_script_path}"
        cmd = ["python3", abs_script_path] + arguments
        try:
            completed = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
            )
            if completed.returncode != 0:
                err = completed.stderr or completed.stdout or "(无输出)"
                return f"执行Python脚本 {script_path} 失败: {err}"
            return f"执行Python脚本 {script_path} 成功: {completed.stdout or '(无输出)'}"
        except subprocess.TimeoutExpired:
            return f"执行Python脚本超时: {script_path}"
        except Exception as e:
            return f"执行Python脚本发生异常: {e}"

    def request_load_skill_permission(self, skill_name: str):
        user_input = input(f"是否运行加载skill {skill_name} (Y/N): ")
        return user_input.upper() == "Y"