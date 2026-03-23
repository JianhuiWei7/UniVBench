from huggingface_hub import snapshot_download

local_save_path = "./UniVBench"

print(f"Downloading dataset to {local_save_path} ...")

snapshot_download(
    repo_id="JianhuiWei/UniVBench",
    repo_type="dataset",
    local_dir=local_save_path,
    local_dir_use_symlinks=False  
)

print("Dataset download completed!")
