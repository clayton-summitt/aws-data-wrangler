import logging

import boto3
import pytest

import awswrangler as wr
from awswrangler.s3._fs import S3Object

logging.getLogger("awswrangler").setLevel(logging.DEBUG)


@pytest.mark.parametrize("mode", ["r", "rb"])
def test_read_text_full(path, mode):
    client_s3 = boto3.client("s3")
    path = f"{path}0.txt"
    bucket, key = wr._utils.parse_path(path)
    text = "AHDG*AWY&GD*A&WGd*AWgd87AGWD*GA*G*g*AGˆˆ&ÂDTW&ˆˆD&ÂTW7ˆˆTAWˆˆDAW&ˆˆAWGDIUHWOD#N"
    client_s3.put_object(Body=text, Bucket=bucket, Key=key)
    with S3Object(path, mode=mode, block_size=100, newline="\n") as s3obj:
        if mode == "r":
            assert s3obj.read() == text
        else:
            assert s3obj.read() == text.encode("utf-8")
    if "b" in mode:
        assert s3obj._cache == b""


@pytest.mark.parametrize("mode", ["r", "rb"])
@pytest.mark.parametrize("block_size", [100, 2])
def test_read_text_chunked(path, mode, block_size):
    client_s3 = boto3.client("s3")
    path = f"{path}0.txt"
    bucket, key = wr._utils.parse_path(path)
    text = "0123456789"
    client_s3.put_object(Body=text, Bucket=bucket, Key=key)
    with S3Object(path, mode=mode, block_size=block_size, newline="\n") as s3obj:
        if mode == "r":
            for i in range(3):
                assert s3obj.read(1) == text[i]
        else:
            for i in range(3):
                assert s3obj.read(1) == text[i].encode("utf-8")
        if "b" in mode:
            assert len(s3obj._cache) <= block_size
    if "b" in mode:
        assert s3obj._cache == b""


@pytest.mark.parametrize("mode", ["r", "rb"])
@pytest.mark.parametrize("block_size", [1, 2, 3, 10, 23, 48, 65, 100])
def test_read_text_line(path, mode, block_size):
    client_s3 = boto3.client("s3")
    path = f"{path}0.txt"
    bucket, key = wr._utils.parse_path(path)
    text = "0\n11\n22222\n33333333333333\n44444444444444444444444444444444444444444444\n55555"
    expected = ["0\n", "11\n", "22222\n", "33333333333333\n", "44444444444444444444444444444444444444444444\n", "55555"]
    client_s3.put_object(Body=text, Bucket=bucket, Key=key)
    with S3Object(path, mode=mode, block_size=block_size, newline="\n") as s3obj:
        for i, line in enumerate(s3obj):
            if mode == "r":
                assert line == expected[i]
            else:
                assert line == expected[i].encode("utf-8")
            if "b" in mode:
                assert len(s3obj._cache) < (len(expected[i]) + block_size)
        s3obj.seek(0)
        lines = s3obj.readlines()
        if mode == "r":
            assert lines == expected
        else:
            assert [line.decode("utf-8") for line in lines] == expected
    if "b" in mode:
        assert s3obj._cache == b""
