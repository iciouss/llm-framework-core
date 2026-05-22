import re


def define_env(env):
    @env.macro
    def env_table(filepath=".env.example"):
        try:
            with open(filepath, "r") as f:
                lines = f.readlines()
        except FileNotFoundError:
            return "File not found."

        # Table headers
        md = "| Variable | Required | Default | Description |\n| :--- | :---: | :--- | :--- |\n"

        description_lines = []
        var_pattern = re.compile(r"^(#\s*)?([A-Za-z0-9_]+)=(.*)$")

        for line in lines:
            line = line.strip()

            if not line:
                description_lines = []
                continue

            match = var_pattern.match(line)

            if match:
                is_commented = bool(match.group(1))
                key = match.group(2)
                val = match.group(3).strip()

                desc = " ".join(description_lines)

                is_required = False
                if "[required]" in desc.lower() or (not is_commented and val == ""):
                    is_required = True

                # FIX: Strictly remove ONLY [Required] or [Optional] with the brackets
                desc = re.sub(r"(?i)\[(required|optional)\]\s*:?\s*", "", desc).strip()

                req_str = "**Yes**" if is_required else "No"

                key_str = f'<code style="white-space: nowrap;">{key}</code>'
                val_str = (
                    f'<code style="white-space: nowrap;">{val}</code>'
                    if val
                    else "_None_"
                )

                md += f"| {key_str} | {req_str} | {val_str} | {desc} |\n"

                description_lines = []

            elif line.startswith("#"):
                clean_comment = line.lstrip("#").strip()
                if clean_comment:
                    description_lines.append(clean_comment)

        return md
