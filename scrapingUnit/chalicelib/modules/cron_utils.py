import boto3
s3_client = boto3.client("s3")


# works to only get us key/file information
def get_key_info(bucket="pubmed", prefix="jobs/"):
    print(f"Getting S3 Key Name, Size and LastModified from the Bucket: {bucket} with Prefix: {prefix}")

    key_names = []
    file_timestamp = []
    kwargs = {"Bucket": bucket, "Prefix": prefix}
    while True:
        response = s3_client.list_objects_v2(**kwargs)
        if "Contents" in response:
            for obj in response["Contents"]:
                # exclude directories/folder from results
                if not obj['Key'].endswith("/"):
                    key_names.append(obj["Key"])
                    file_timestamp.append(obj["LastModified"].timestamp())
        else:
            break

        try:
            kwargs["ContinuationToken"] = response["NextContinuationToken"]
        except KeyError:
            break

    key_info = {
        "key_path": key_names,
        "timestamp": file_timestamp,
    }
    print(f'All Keys in {bucket} with {prefix} Prefix found!')

    return key_info


# Check if date passed is older than date limit
def check_expiration(key_date=0, limit=0):
    if key_date < limit:
        return True


# connect to s3 and delete the file
def delete_s3_file(file_path, bucket="pubmed"):
    print(f"Deleting {file_path}")
    # result = subprocess.run([f'aws s3 rm s3://{bucket}/{file_path}'], shell=True, capture_output=True, text=True)
    # print(result.stdout)
    s3_client.delete_object(Bucket=bucket, Key=file_path)
    return True


# delete all files in the subfolder in bucket with prefix
def delete_s3_files_in_folder(bucket, prefix, expire_limit):
    s3_file = get_key_info(bucket=bucket, prefix=prefix)
    for i, fs in enumerate(s3_file["timestamp"]):
        file_expired = check_expiration(fs, expire_limit)
        if file_expired:
            delete_s3_file(s3_file["key_path"][i], bucket)
