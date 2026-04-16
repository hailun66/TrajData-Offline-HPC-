import sys
import os
sys.path.insert(0, "/storage/public/home/250054/trajdata/src")

from trajdata import UnifiedDataset

# ==========================================
# 1. 配置超算上的数据集路径 (请根据你的实际路径修改)
# ==========================================
DATA_ROOT = "/storage/public/home/250054/trajdata"

dataset_dirs = {
   # --- NuScenes 全量 ---
    # 根据 DATASETS.md，指向包含 v1.0-trainval 等子文件夹的根目录
    "nusc_trainval": os.path.join(DATA_ROOT, "NuScenes"),
    "nusc_test": os.path.join(DATA_ROOT, "NuScenes"),
    "nusc_mini": os.path.join(DATA_ROOT, "NuScenes"),
    
    # --- Waymo 全量 ---
    # 指向包含 training, validation 子文件夹的根目录
    "waymo_train": os.path.join(DATA_ROOT, "waymo_motion"),
    "waymo_val": os.path.join(DATA_ROOT, "waymo_motion"),
    "waymo_test": os.path.join(DATA_ROOT, "waymo_motion"),
    
    # --- nuPlan 全量 ---
    # 指向 nuPlan 的根目录 (包含 maps 和 nuplan-v1.1 子文件夹)
    "nuplan_mini": os.path.join(DATA_ROOT, "nuplan/dataset/nuplan-v1.1"),
    
    # --- Lyft 全量 ---
    # 注意：Lyft 必须精确指向具体的 .zarr 文件夹 (参考 dataset.py 中的写法)
    "lyft_train": os.path.join(DATA_ROOT, "lyft_data/scenes/train.zarr"),
    "lyft_val": os.path.join(DATA_ROOT, "lyft_data/scenes/validate.zarr"),
    "lyft_train_full":os.path.join(DATA_ROOT,"lyft_data/scenes/train_full.zarr"),
    "lyft_sample":os.path.join(DATA_ROOT,"lyft_data/scenes/sample.zarr"),
    
    # --- Argoverse 2 全量 ---
    # 指向包含 train, val 子文件夹的根目录
    "av2_motion_forecasting": os.path.join(DATA_ROOT, "Argoverse2"),
    
    # --- Interaction 全量 (暂不包含 lanelet2 时请保持注释) ---
    # "interaction_single": os.path.join(DATA_ROOT, "interaction_single"),
    # "interaction_multi": os.path.join(DATA_ROOT, "interaction_multi"),
}

# ==========================================
# 2. desired_data: 指定需要提取的具体划分 (Splits)
# ==========================================
desired_data = [
    # 提取 NuScenes 全量的训练集和验证集
    "nusc_trainval-train",
    # "nusc_test-test", # 👈没有标注，没有ground truth，用不了
    "nusc_mini-mini_train",
    "nusc_mini-mini_val",
    
    # 提取 Waymo 的训练集和验证集
    "waymo_train-train",
    "waymo_val-val",
    # "waymo_test-test", # 👈没有标注，没有ground truth，用不了
    
    # 提取 nuPlan 全量的训练集和验证集
    # "nuplan_trainval-train",
    # "nuplan_trainval-val",
    "nuplan_mini-mini_train",
    "nuplan_mini-mini_val",
    # "nuplan_mini-mini_test", # 👈没有标注，没有ground truth，用不了
    
    # 提取 Lyft 全量训练集和验证集
    "lyft_train-train",
    "lyft_val-val",
    "lyft_train_full-train",
    "lyft_sample-mini_train",
    
    # 提取 Argoverse 2 全量的训练集和验证集
    "av2_motion_forecasting-train",
    "av2_motion_forecasting-val",
    # "av2_motion_forecasting-test", # 👈没有标注，没有ground truth，用不了
    
    # (如果后续解决了 lanelet2 依赖，再放开 Interaction)
    # "interaction_single-train",
    # "interaction_single-val",
    # "interaction_multi-train",
    # "interaction_multi-val",
]

# ==========================================
# 3. 配置并初始化 UnifiedDataset
# ==========================================
print("🚀 初始化 Unified Dataset，准备开始构建统一缓存数据库...")

# 超算上建议指定一个高速的 SSD 缓存目录，如 /scratch 节点
CACHE_DIR = "/storage/public/home/250054/trajdata/trajdata_unified_cache"

dataset = UnifiedDataset(
    desired_data=desired_data,
    data_dirs=dataset_dirs,
    cache_location=CACHE_DIR,
    # 启用多进程加速数据转换，根据你申请的超算节点 CPU 核心数设置
    num_workers=32, 
    # 是否强制重新创建缓存（如果以前建过一半失败了，可以设为True）
    rebuild_cache=False,
    # 需要提取的智能体类型（车辆、行人、自行车等），这对于研究跨越交通参与者的交互至关重要
    desired_dt=0.1, # 统一重采样到 10Hz (0.1s)，这对量化对比极其重要！
    standardize_data=True # 强制转换为 trajdata 的标准化坐标系和单位
)

print(f"✅ 统一数据库已构建完毕！总计包含 {len(dataset)} 个有效轨迹场景 (Scenes)。")
print(f"📁 统一缓存已存储至: {CACHE_DIR}")

# 将生成器先转换为 list，再取第一个场景测试
scenes_list = list(dataset.scenes())
if len(scenes_list) > 0:
    sample_scene = dataset.get_scene(scenes_list[0].name)
    print(f"🔍 验证场景数据: {sample_scene.name}, 包含 {len(sample_scene.agents)} 个交通参与者。")