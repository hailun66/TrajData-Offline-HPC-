# TrajData-Offline-HPC-
🚗本仓库提供了一套经过完整实战检验的解决方案，旨在帮助研究人员在完全断网的高性能计算集群（HPC）上，使用 trajdata 提取并统一五大主流自动驾驶数据集（Waymo, nuScenes, nuPlan, Lyft, Argoverse 2）的轨迹与交互数据。

🌟 为什么需要这个仓库？
离线环境的噩梦：超算节点通常无法连接外网。官方依赖包中夹杂了大量冗余的云端拉取组件（如 AWS S3）、绘图包和严苛的版本锁，直接导致离线安装困难重重。
统一的格式与基座：将来自不同机构、坐标系各异的千万级原始轨迹，统一转换为标准的 10Hz (.sqlite/.pkl) 数据流，实现跨数据集的模型训练与泛化测试。
修复了多个官方源码中导致跑批中断的隐蔽 Bug（如 Waymo 测试集的空地图崩溃、Lyft 的 Numpy 版本冲突等）。

📦 包含的数据集与规模
通过本指南，你将获得一个包含以下数据的终极缓存库（Cache）：
	Waymo Open Motion (全量 Train/Val)
	nuPlan (Mini/全量)
	nuScenes (全量 Trainval/Test/Mini)
	Lyft Level 5 (全量 Train/Val)
	Argoverse 2 (全量 Train/Val)

🛠️ Step-by-Step 离线安装指南
1. 基础环境准备
在有网的本地机器上下载对应版本的包，并上传至超算的 trajdata_offline_pkgs 目录中：

Bash
	# 创建纯净环境
	conda create -n trajdata_env python=3.10 -y
	conda activate trajdata_env

2. 核心包 trajdata 与基础依赖安装
在包含 .whl 文件的目录下执行：

Bash
# 避免安装导致冲突的旧版 numpy
pip install --no-index --find-links . trajdata-1.4.0-py3-none-any.whl
(注：如果由于依赖链过深导致缺失，请在本地使用 pip download <pkg> --platform manylinux2014_x86_64 --python-version 310 --only-binary=:all: 下载后上传安装。)

3. 数据集专属“地雷”与破解方案
💣 坑 1: Waymo TF依赖与 NumPy 降级冲突
Waymo 的官方解析包强行绑定了特定的 TensorFlow 和过低的 Numpy 版本。
破解：直接无视它关于 plotly, visu3d 等可视化包缺失的报错（我们只提取数据不需要绘图）。

💣 坑 2: NuPlan 的无尽依赖地狱 (云端组件与地图解析)
NuPlan 官方包强制需要 AWS 云端组件，且在离线安装时容易遗漏核心配置文件。
破解：

强制安装：pip install --no-deps nuplan-devkit-xxxx.whl

手动补齐栅格与地图库：离线安装 rasterio, rtree。

手动补齐 AWS 库：离线安装 aioboto3, wrapt, retry。

手动补齐配置文件：从源码中拷贝丢失的 .yaml 文件：

Bash
cp -r nuplan-devkit/nuplan/planning/script/* ~/miniconda3/envs/trajdata_env/lib/python3.10/site-packages/nuplan/planning/script/
💣 坑 3: Argoverse 2 无法识别 (名称校验错误)
虽然 trajdata 内部包含 AV2 解析器，但对名称有严格白名单校验。
破解：在配置文件中，data_dirs 的键名必须严格命名为 "av2_motion_forecasting"。

🚀 运行数据构建脚本
参考本仓库提供的 build_unified_db.py。
配置好你的路径后，强烈建议使用 SLURM 后台提交，或使用 nohup 运行（因为全量处理通常需要 10-20 小时）。

Bash
sbatch submit_db_build.sh
⚠️ 运行中的致命崩溃点与修复 (Hotfixes)
在跑批阶段，由于数据量极大，原源码中的几个 Bug 会导致整个多进程池崩溃（OOM 或抛错）。请在运行前修复：

Waymo Test 场景空地图崩溃 (ValueError: cannot convert float NaN to integer)

原因：极个别 Test 场景无地图数据，导致栅格化计算 NaN。

解决：在 desired_data 列表中直接注释掉 "waymo_test-test"（测试集无标签，通常不需要）。

备选方案：修改 trajdata/utils/raster_utils.py 第 146 行，加入对 NaN 的拦截。

Lyft Numpy 报错 (AttributeError: module 'numpy' has no attribute 'float')

原因：Numpy 1.20+ 弃用了 np.float，而 Lyft 官方 l5kit 仍在使用。

解决：编辑环境中的 l5kit/data/map_api.py 第 399 行，将 dtype=np.float 更改为 dtype=float。

NuPlan 地图路径找不到 (AssertionError: .../nuplan/maps does not exist!)

原因：底层按固定层级向父目录寻找 maps 文件夹。

解决：传入的字典路径必须深至 nuplan-v1.1，例如："nuplan_mini": "/path/to/dataset/nuplan-v1.1"。

NuScenes/NuPlan Mini 划分找不到

原因：官方将 mini 进一步切分。

解决：后缀必须写为 mini_train 和 mini_val（例如 "nuplan_mini-mini_train"）。

📖 如何使用构建好的统一缓存？
提取完成后，你可以让你的代码直接读取该缓存（无需再次读取原始繁杂的文件夹）：

Python
from trajdata import UnifiedDataset

dataset = UnifiedDataset(
    desired_data=["waymo_train-train", "nusc_trainval-train"],
    data_dirs={}, # 无需原始数据
    cache_location="/path/to/your/trajdata_unified_cache", # 👈 指向你生成的宝库
    rebuild_cache=False # 直接读取
)

print(f"Total scenes available: {len(dataset)}")
🤝 贡献与致谢
感谢 trajdata 团队提供了卓越的统一基座抽象。本仓库旨在解决离线集群环境下的最后一公里工程问题。欢迎提 Issue 补充更多边缘场景的 Bug 修复！
