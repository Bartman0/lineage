from lineage import inspect_lineage


@inspect_lineage("a_groupby_c")
def do_join():
    df = df1.select('a').groupby('c')
    df3 = df.sum()
    df4 = df3.join(df1)
    return df4

@inspect_lineage("s3_read")
def read_s3_partitions(environment, branch, schemaname, tablename, bucket):
    bucket = get_bucket_name(environment, branch, schemaname, tablename, bucket)
    logger.debug("bucket: " + bucket)
    prefix = PARTITION_PREFIX  # PARTITION_COLUMN + "="
    result = set()
    for partition in get_matching_s3_keys(bucket, prefix=prefix):
        logger.debug("partition candidate: " + partition)
        try:
            partition_value = partition.split('/', 2)[0][len(prefix):]
            datetime.strptime(partition_value, PARTITION_FORMAT)
            result.add(partition_value)
            logger.debug("partition matched: " + partition_value)
        except ValueError:
            logger.warning(f"can not parse partition value for S3 key [{partition}]")
    return result


do_join()

