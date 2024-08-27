import boto3
from config import bucket_name

def get_tool_spec():
    """
    Returns the tool specification for the SaveToS3Tool.

    :return: The tool specification for the SaveToS3Tool.
    """
    return {
        "toolSpec": {
            "name": "SaveToS3Tool",
            "description": "Save the input code to the s3 bucket.",
            "inputSchema": {
                "json": {
                    "type": "object",
                    "properties": {
                        "code": {
                            "type": "string",
                            "description": "The code to be saved",
                        },
                    },
                    "required": ["code"],
                }
            },
        }
    }


def SaveToS3(code):
    """
    Saves the input code to the s3 bucket.
    ::param code: The code to be saved.
    ::return: The output of the save
    """
    file_code = code
    s3_client = boto3.client('s3')
    file_name = "backend.py"
    s3_client.put_object(
        Bucket=bucket_name,
        Key=file_name,
        Body=file_code
    )
    return {
        'statusCode': 200,
        'body': f"Output saved to s3://{bucket_name}/{file_name}"
    }