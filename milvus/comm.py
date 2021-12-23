from pymilvus import connections, FieldSchema, CollectionSchema, DataType, Collection
import random
from loguru import logger as logger


indexTypeMapping={}

hnswParams={"M": 4, 'efConstruction': 13}
indexTypeMapping['HNSW']=hnswParams
flatParams={}
indexTypeMapping['FLAT']=hnswParams

IVF_FLATParams={'nlist':100}
indexTypeMapping['IVF_FLAT']=IVF_FLATParams

indexSearchParams={}
hnswSearchParams={'ef':300}
indexSearchParams['HNSW']=hnswSearchParams

IVF_FLATSearchParams={'nprobe':5}
indexSearchParams['IVF_FLAT']=IVF_FLATSearchParams

flat_FLATSearchParams={}
indexSearchParams['FLAT']=IVF_FLATSearchParams




hnswParams={"M": 4, 'efConstruction': 13}
indexTypeMapping['HNSW']=hnswParams

def milvusTest(params=None):
    collectionName=params.get('collectionName')
    assert collectionName is not None
    opName = params.get('opName', 'query')
    assert opName is not None
    #FLAT, IVF_FLAT, IVF_SQ8, IVF_PQ, HNSW
    indexType=params.get('indexType','HNSW')

    featuresNum=params.get('featuresNum',30000)
    #query,build,delete

    #only support two partitionName
    partitionNames=params.get('partitionNames',[])
    shardNum=params.get('shardNum',0)
    #IP
    metric_type=params.get('metric_type','L2')
    dimNum = params.get('dimNum',1280)

    connections.connect(host='10.16.210.148', port='19532')

    if opName == 'build':
        logger.info('start to build index, params: {}',params)
        default_fields = [
            FieldSchema(name="pId", dtype=DataType.INT64, is_primary=True),
            FieldSchema(name="random_value", dtype=DataType.DOUBLE),
            FieldSchema(name="features", dtype=DataType.FLOAT_VECTOR, dim=dimNum)
        ]
        default_schema = CollectionSchema(fields=default_fields, description="test collection")

        collection = Collection(name=collectionName, schema=default_schema, shards_num=shardNum)
        logger.info('create partitions:{}',partitionNames)
        for p in partitionNames:
            collection.create_partition(partition_name=p)
        indexBuildParams=indexTypeMapping.get(indexType)
        logger.info('index params:',indexBuildParams)
        default_index = {"index_type": indexType, "params": indexBuildParams, "metric_type": metric_type}
        collection.create_index(field_name="features", index_params=default_index)
        batchAddNum = 1000
        d = 0
        partitionName=None
        for i0 in range(0, featuresNum, batchAddNum):

            if len(partitionNames)==2:
                partitionName = partitionNames[d % 2]
                if d == 0:
                    d = 1
                else:
                    d = 0




            i1 = min(featuresNum, i0 + batchAddNum)
            vectors = [[random.random() for _ in range(dimNum)] for _ in range(i1 - i0)]

            logger.info("  adding %d:%d / %d" % (i0, i1, featuresNum))
            if partitionName is None:
                insertResult = collection.insert(
                    [
                        [i for i in range(i0, i1, 1)],
                        [float(random.randrange(-20, -10)) for _ in range(i0, i1, 1)],
                        vectors
                    ]
                )
            else:
                insertResult = collection.insert(
                    [
                        [i for i in range(i0, i1, 1)],
                        [float(random.randrange(-20, -10)) for _ in range(i0, i1, 1)],
                        vectors
                    ], partition_name=partitionName
                )



            logger.info(insertResult.primary_keys)
        totalNum = collection.num_entities
        logger.info('finished insert features, totalNum:{}', totalNum)

    elif opName == 'query':
        collection = Collection(collectionName)

        collection.load()
        topK = 5
        search_params = indexSearchParams.get(indexType,None)
        search_params={"metric_type": "L2", "params": search_params}
        query_vectors = [[random.random() for _ in range(dimNum)] for _ in range(2)]
        partitionNames.append('_default')
        for p in partitionNames:

            print('partitionName: ' + p)
            logger.info('query partitionName: {}, search_params:{}',p,search_params)
            res = collection.search(
                query_vectors[-1:], "features", search_params, topK,
               output_fields=["pId", "random_value"], partition_names=[p]
            )
            for raw_result in res:
                for result in raw_result:
                    id = result.id  # result id
                    distance = result.distance
                    logger.info('id:{},distance:{}',id,distance)
                    # expr = "pk in ['"+str(id)+"']"
                    #
                    # collection.delete(expr)
                    logger.info(result)

    else:
        raise Exception('not supported opName:%s' % opName)









def testIndexWithPartition(params=None):
    '''

    :param params:
    opType: query ,create or delete

    query: collectionName
    create: collectionName, partitionNames
    delete:
    :return:
    '''


def testIndex(opType=None):
    # check if existed if existed drop collection
    # create index
    # query index
    indexType='HNSW'
    # index_type="IVF_FLAT"
    if opType == 'create':
        vectorNum = 40000
    if opType == 'query':
        vectorNum = 10



    collectionName = "hnswTest_128_40000_withPartitionNames1"
    connections.connect(host='10.16.210.148', port='19532')
    dim = 1280

    partitionNames=['p1','p2']



    if opType=='create':
        default_fields = [
            FieldSchema(name="count", dtype=DataType.INT64, is_primary=True),
            FieldSchema(name="random_value", dtype=DataType.DOUBLE),
            FieldSchema(name="float_vector", dtype=DataType.FLOAT_VECTOR, dim=dim)
        ]
        default_schema = CollectionSchema(fields=default_fields, description="test collection")

        collection = Collection(name=collectionName, schema=default_schema, shards_num=2)
        for p in partitionNames:
            collection.create_partition(partition_name=p)


        default_index = {"index_type": indexType, "params": {"M": 4, 'efConstruction': 13}, "metric_type": "L2"}
        collection.create_index(field_name="float_vector", index_params=default_index)
        batchAddNum = 1000
        d=0
        for i0 in range(0, vectorNum, batchAddNum):
            partitionName=partitionNames[d%2]
            if d==0:
                d=1
            else:
                d=0
            i1 = min(vectorNum, i0 + batchAddNum)
            vectors = [[random.random() for _ in range(dim)] for _ in range(i1 - i0)]

            print("  adding %d:%d / %d" % (i0, i1, vectorNum))
            insertResult=collection.insert(
                [
                    [i for i in range(i0, i1, 1)],
                    [float(random.randrange(-20, -10)) for _ in range(i0, i1, 1)],
                    vectors
                ],partition_name=partitionName
            )
            print(insertResult)
    else:
        collection=Collection(collectionName)
    totalNum=collection.num_entities
    print('totalNum:%s' % totalNum)
    collection.load()
    topK = 5
    search_params = {"metric_type": "L2", "params": {"ef": 10}}
    query_vectors = [[random.random() for _ in range(dim)] for _ in range(2)]
    for p in partitionNames:
        print('partitionName: '+p)
        res = collection.search(
            query_vectors[-1:], "float_vector", search_params, topK,
            "count > 3 and random_value in [-11]", output_fields=["count", "random_value"],partition_names=[p]
        )
        for raw_result in res:
            for result in raw_result:
                id = result.id  # result id
                distance = result.distance
                # expr = "pk in ['"+str(id)+"']"
                #
                # collection.delete(expr)
                print(id, distance)
                print(result)






    # collection.drop()




if __name__ == "__main__":


    params={}
    params['collectionName']='milvusTest1_FLAT'
    params['indexType']='FLAT'
    # params['opName'] = 'build'
    params['opName'] = 'query'

    milvusTest(params=params)












