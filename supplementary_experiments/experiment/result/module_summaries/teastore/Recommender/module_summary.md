# teastore / Recommender
## 模块职责
Teastore项目的独立个性化推荐服务模块，核心负责基于历史订单生成用户个性化商品推荐，同时集成Kieker链路监控数据采集子模块，提供推荐模型训练管理、REST服务暴露、性能监控数据采集能力，支撑商城个性化推荐业务与性能分析。
## 核心功能
1. 多算法推荐：内置流行度推荐、订单关联推荐、基础/预计算优化版SlopeOne协同过滤推荐，支持算法配置化选型与异常自动降级兜底
2. 可扩展算法框架：定义统一推荐算法接口，抽象封装数据预处理、结果过滤等通用逻辑，支持快速扩展新算法
3. 多模式模型训练：支持启动自动训练、手动触发训练、后台守护线程定期重训练三种模式，提供训练状态与数据时间戳查询能力
4. REST服务暴露：提供批量推荐、单商品推荐两类业务接口，以及训练控制、状态查询两类管理接口
5. 服务治理：支持启动等待依赖服务就绪、自动服务注册注销，保障服务可用性
6. Kieker监控数据采集：从RabbitMQ消费Kieker链路监控记录，提供内存缓存、本地落盘持久化，以及Web端监控数据查看、管理能力，提供REST CRUD端点抽象简化业务接口开发
## 主要代码区域
1. 核心算法层：`tools.descartes.teastore.recommender.algorithm`，包含统一推荐接口`IRecommender`、通用逻辑抽象基类`AbstractRecommender`、算法选择与降级组件`RecommenderSelector`，以及各类算法实现类
2. REST服务层：`tools.descartes.teastore.recommender.rest`，包含`RecommendEndpoint`（批量推荐）、`RecommendSingleEndpoint`（单商品推荐）、`TrainEndpoint`（训练管理）三类端点，继承自监控子模块提供的`AbstractCRUDEndpoint`
3. 启动与训练协调层：`tools.descartes.teastore.recommender.servlet`，包含启动引导`RecommenderStartup`、定期重训练守护线程`RetrainDaemon`、训练协调器`TrainingSynchronizer`
4. Kieker监控子模块：包含`LogReaderDaemon`（RabbitMQ拉取）、`LogConsumer`（数据消费）、`MemoryLogStorage`（内存缓存）、`FileWriterDaemon`（落盘守护）、`LogReaderStartup`（生命周期管理），以及`IndexServlet`、`DisplayLogs`、`Reset`三类监控管理Web端点
5. 公共依赖：依赖项目公共层`tools.descartes.teastore.entities`提供业务实体定义
## 与其他模块的交互
1. 依赖持久化模块`tools.descartes.teastore.persistence`拉取历史订单、商品数据用于推荐模型训练，通过服务注册发现组件完成服务对接
2. 依赖Kieker监控框架做性能分析，依赖RabbitMQ获取监控数据，依赖Servlet容器提供Web/REST服务运行环境
3. 依赖项目公共实体层提供基础数据结构，依赖项目工具层提供Kieker探针、Docker内存配置工具支撑
4. 对外通过REST接口暴露推荐服务与训练管理能力，供商城前端或其他业务模块调用
5. 监控子模块为整个Recommender模块提供性能追踪数据支撑，其提供的抽象基类支撑业务REST端点开发
## 架构识别线索
1. 独立部署的微服务模块，通过REST接口对外提供能力，符合微服务架构拆分模式
2. 算法层实现了策略模式，通过统一接口抽象支持多算法可替换、可扩展，支持动态配置选型
3. 内置降级容错设计，算法异常自动 fallback 到基础兜底算法，提升服务可用性
4. 拆分清晰的分层架构：实体依赖层->核心算法层->服务层->启动调度层，职责分离清晰
5. 集成了完整的可观测性支撑，内置监控数据采集模块支撑性能分析，符合云原生微服务可观测性设计要求
