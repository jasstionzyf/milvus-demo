## milvus 安装及使用
### 向量搜索应用场景
```
多模态搜索
向量以及传统的搜索结合
```

#### 系统环境要求
```
linux系统
推荐使用ubuntu 20.04 LTS
```
#### 架构介绍
```
milvus主要组件:
1: Etcd 主要是存储milvus集群的元信息
2: Pulsar: 起到解耦各个服务组件的作用
3: MinIO: 主要是保存原始vector以及产生的索引
4: Milvus core (a executable binary file，主程序)
```
#### 安装配置
```
系统依赖安装:
go install
apt package libopenblas-dev libgomp1 libtbb2 make
openblas install
go: 1.15
cmake: >=3.18
gcc: 7.5
protobuf: >=3.7


etcd, pulsar以及minio都有官方安装文档，这里不再介绍，
主要介绍milvus的安装以及配置,假设etcd,pulsar以及minio安装完毕.

install from source
我在ubuntu上编译了milvus 可执行文件，直接可以部署在ubuntu 20.04服务器上
你也可以直接自己重新从从源码编译，文档:
https://github.com/milvus-io/milvus#to-start-developing-milvus
编译完成之后除了milvus可执行binary文件之外， 还有milvus运行依赖的so 文件，
比如:
fiu_posix_preload.so
fiu_run_preload.so
libfaiss.so ...
需要将放在/usr/lib下面
milvuis启动的时候会加载这些so libary如果配置有问题会报错

配置:
每个节点的配置文件milvus.yaml中配置etcd,minio以及pulsar的endpoints即可.
配置文件demo: https://github.com/milvus-io/milvus/blob/master/configs/milvus.yaml
启动直接执行: start_cluster.sh
执行脚本: https://github.com/milvus-io/milvus/tree/master/scripts/start_cluster.sh
这个执行脚本会启动milvus里面的所有组件:
rootcoord
datacoord
querycoord
indexcoord
datanode
querynode
indexnode
proxy


个人写的ansible 运维脚本:
支持部署milvus分布式集群
https://github.com/jasstionzyf/app_ansible.git


```
### client libary 以及命令行工具
```
https://github.com/milvus-io/pymilvus
https://github.com/milvus-io/milvus_cli



```
### milvus的几个重要的concept
```
Primary Id:
milvus里面每个entity都必须有一个pid(primary id)，类型必须是scala类型的，必须
int,long,或者double等
如果创建collection的时候不设置pid,则milvus会自动给每个entity 设置一个自增长的pid.

Partition:
一个collection中可以分几个partition，虽然每个partition里面保存的entity结构一致，
但是查询的时候可以指定某个partition进行查询，类似于查询中的过滤功能，这样能够提高查询的效率
如果制定了partition，那么插入的时候也需要指定partition
默认只有一个partition: _default

Shard:
类似于es中的副本的概念，
对于每个partition，milvus可以根据shardNum创建多个副本，来提升读的性能。
默认是1，每个collection创建之后只有一个shard对应每个partition
如果指定了，则每个collection的每个partition则会有shardNum个副本可以共查询.
Segments:
类似于es中的lucene segments
每个collection会有多个partition，每个partition会有多个segments,
每个segments milvus会根据参数决定是创建index，如果没有触发条件，则
直接载入内存进行暴力搜索

Hybrid Search:，
search的时候指定expr
expr是一个boolean表达式，可以组合任意的entity的scala fields
具体语法可以参考: https://milvus.io/docs/boolean.md

Time Travel Search


channel:
每个组件之间的协作都是通过订阅相关的channel来进行协作，
channel可以理解为类似kafka 的topics
DML-Channel
```
#### 索引类型选择
```
FLAT, IVF_FLAT, IVF_SQ8, IVF_PQ, HNSW
推荐大家使用
FLAT: 如果需要100%的recall而且根据数据大小能够容忍速度慢，而且数据集不会操作milvus的大小
IVF_FLAT: 相比FLAT以及HNSW，内存占有降低很多，但是recall下降比较多
build参数: nlist
query参数: nprobe


HNSW: 内存充裕的情况下优先使用，和FLAT使用内存相似的情况下，速度提升很多，而且召回率仅仅略有下降
build 参数: m=4,efConstruction=13
query 参数: ef=300
论文: https://deepai.org/publication/a-comparative-study-on-hierarchical-navigable-small-world-graphs
```

#### 测试代码项目
```
https://github.com/jasstionzyf/milvus-demo.git
```

### Milvus 优缺点以及和其他向量检索框架的对比
```
优点:
1: 使用简单易上手
2: 计算存储分离，读写分离，架构理论上能保证很好的可扩展性
3: 社区很活跃，每天提交的pull request 都是十几个左右
缺点:
1: 项目比较年轻，2022-01-27 刚实现一个GA 版本
2: 因为目前仅仅支持向量搜索以及简单的字段的过滤，和传统的搜索结合起来不是那么方便，必须客户端这边在重新进行过滤排序


其他的检索框架，比如: faiss, nmslib等，基本上都是单机版本，可扩展性不行

完美的向量搜索框架？
能够在传统搜索引擎的基础上原生整合实现，比如elasticsearch
，然后能够直接将向量的查询结果和一般的搜索结果直接在es内部高效进行过滤
即提高了复杂检索的效率，同时也降低了系统运维维护的开销，
同时避免了技术的重新投入，直接使用原有的es dsl query即可

es:
1: 支持通过script score 的方式进行exeactly match
2: es 8.0 借助于lucene 9.0实现了基于hnsw算法的向量搜索，
但是不支持搜索结果和一般搜索结果的整合过滤

opensearch:
基于faiss以及nmslib开源框架实现， 通过java 调用c++ so库文件实现，
支持filter功能



```
