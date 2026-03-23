from huggingface_hub import snapshot_download

local_save_path = "./downloaded_benchmark"

print(f"Downloading dataset to {local_save_path} ...")

# 下载整个数据集仓库的原始文件
snapshot_download(
    repo_id="JianhuiWei/UniVBench",
    repo_type="dataset",
    local_dir=local_save_path,
    local_dir_use_symlinks=False  # 设为 False 以确保下载的是实体文件而非软链接
)

print("Dataset download completed!")
