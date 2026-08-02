# hadoop / YARN
## 模块职责
YARN是Hadoop的资源管理与作业调度核心模块，负责集群统一资源管理、应用生命周期管理、容器调度执行，支撑分布式计算作业运行，并提供可观测性、安全管控、高可用与生态扩展能力，采用分层RPC通信+事件驱动架构实现核心组件解耦。
## 核心功能
1. **核心API与通信协议**：定义客户端、ResourceManager(RM)、ApplicationMaster(AM)、NodeManager(NM)四类核心角色的RPC交互协议，基于Protobuf实现全场景请求/响应数据结构的序列化，统一YARN核心领域模型（应用、应用尝试、容器、节点、资源）的标识与抽象。
2. **公共基础支撑**：提供事件驱动框架、通用状态机、统一服务生命周期管理、可扩展对象工厂、RPC通信基础设施、安全认证基础体系、通用工具类与嵌入式Web框架，支撑所有YARN上层组件运行。
3. **NodeManager核心能力**：单个工作节点全生命周期管理，负责容器全生命周期执行（启动/停止/清理）、容器资源本地化（按可见性缓存+LRU清理）、节点心跳与状态同步RM、容器资源监控（内存超限检测）、容器日志聚合（上传HDFS）与查询、节点健康检查。
4. **ResourceManager核心能力**：YARN集群全局资源管理入口，负责节点准入与存活管控、应用全生命周期管理、AM启动管控、多策略资源调度（提供FIFO、容量调度两种开箱即用实现）、RM状态持久化与故障恢复（支持内存/ZooKeeper存储）、管理员运行时配置刷新、审计日志能力。
5. **可观测与交互能力**：提供RM、NM两级Web可视化界面，支持集群状态、队列信息、应用/容器状态、日志的查询与交互；提供Web应用代理，安全代理访问各AM的Web界面；提供RMAdmin命令行管理工具支撑集群运维。
6. **生态扩展能力**：提供DistributedShell示例应用、MapReduce开发示例、Eclipse开发插件、HDFS RAID纠删容错、分布式Lucene索引、MapReduce性能诊断工具Vaidya、YARN调度仿真工具Rumen等周边工具与扩展。
## 主要代码区域
| 层级/模块 | 核心路径 |
| ---- | ---- |
| 核心API层 | `hadoop-mapreduce-project/hadoop-yarn/hadoop-yarn-api` | 核心协议、数据模型、PB序列化实现 |
| 公共基础层 | `hadoop-mapreduce-project/hadoop-yarn/hadoop-yarn-common` | 事件、状态机、服务生命周期、RPC、安全、Web框架、工具类 |
| 服务端公共 | `hadoop-mapreduce-project/hadoop-yarn/hadoop-yarn-server/hadoop-yarn-server-common` | RM-NM交互协议、节点健康检查、服务端安全基础 |
| NodeManager | `hadoop-mapreduce-project/hadoop-yarn/hadoop-yarn-server/hadoop-yarn-server-nodemanager` | NM核心、容器管理器、资源本地化、日志聚合、监控、Web服务 |
| ResourceManager | `hadoop-mapreduce-project/hadoop-yarn/hadoop-yarn-server/hadoop-yarn-server-resourcemanager` | RM核心、RPC服务、应用/容器/节点管理、状态恢复、资源调度、安全、Web UI |
| Web代理 | `hadoop-mapreduce-project/hadoop-yarn/hadoop-yarn-server/hadoop-yarn-server-web-proxy` | AM Web界面代理服务 |
| 示例与工具 | `hadoop-mapreduce-project/hadoop-yarn/hadoop-yarn-applications-distributedshell`、`hadoop-mapreduce-project/contrib`、`hadoop-mapreduce-project/examples`、`hadoop-mapreduce-project/tools` | 示例应用、生态扩展工具、仿真工具Rumen |
## 与其他模块的交互
- 依赖`hadoop-common`：依赖Hadoop公共配置、IO、文件系统适配、RPC框架、安全体系、序列化基础能力；
- 依赖`hadoop-hdfs`：依赖HDFS存储容器本地化资源、聚合日志、应用jar包与作业数据；
- 支撑上层MapReduce等计算框架：为MapReduce、Spark等分布式计算框架提供资源调度与容器运行支撑，上层框架通过YARN API提交作业、申请资源；
- 生态工具依赖YARN核心能力：所有扩展示例、诊断、仿真工具都依赖YARN的资源调度、作业运行能力运行，Rumen输出的负载数据为YARN核心调度模块提供仿真测试输入。
## 架构识别线索
1. 分层契约架构：核心API层定义所有跨角色RPC协议与数据模型，下层实现层依赖API契约，符合面向接口的分层设计，核心角色之间通过RPC解耦；
2. 事件驱动+状态机架构：YARN全模块基于事件分发器异步处理状态变更，应用、容器、节点、资源等核心实体都采用有限状态机管理生命周期，实现生产与处理解耦；
3. 可扩展设计：资源调度器抽象顶层接口，支持自定义调度策略；对象工厂支持切换序列化实现；NodeManager支持自定义辅助服务扩展；状态恢复支持扩展不同存储实现；
4. 核心角色拆分：RM负责全局资源管理与调度，NM负责单节点容器执行与监控，AM负责应用内资源协商与任务调度，三类核心职责拆分明确，是典型的中央调度+分布式执行架构。
