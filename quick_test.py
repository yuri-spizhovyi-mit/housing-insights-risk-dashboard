import os


def get_folder_sizes(base_path, label):
    sizes = []
    if not os.path.exists(base_path):
        print(f"⚠️ Skipping {label}: {base_path} not found")
        return sizes

    for pkg in os.listdir(base_path):
        path = os.path.join(base_path, pkg)
        if os.path.isdir(path):
            total_size = 0
            for dirpath, _, filenames in os.walk(path):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    try:
                        total_size += os.path.getsize(fp)
                    except (OSError, FileNotFoundError):
                        pass
            sizes.append((pkg, total_size / (1024 * 1024)))  # MB

    sizes.sort(key=lambda x: x[1], reverse=True)  # largest first
    print(f"\n📦 {label} packages in {base_path} (Top 20 largest):\n")
    for pkg, size in sizes[:20]:
        print(f"{pkg:40} {size:8.2f} MB")
    return sizes


if __name__ == "__main__":
    # Python site-packages (Windows style path)
    get_folder_sizes(".venv/Lib/site-packages", "Python")

    # Node.js dependencies
    get_folder_sizes("node_modules", "Node.js")
