"""
Copyright (C) 2022 Red Hat, Inc. (https://github.com/Commonjava/charon)

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

         http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
from typing import List
from charon.storage import S3Client, CHECKSUM_META_KEY
from charon.utils.archive import extract_zip_all
from charon.utils.files import overwrite_file, read_sha1
from charon.constants import PROD_INFO_SUFFIX
from tests.base import BaseTest, SHORT_TEST_PREFIX
from moto import mock_s3
import boto3
import os
import sys
import zipfile
import shutil

from tests.constants import INPUTS

MY_BUCKET = "my_bucket"
MY_PREFIX = "mock_folder"

COMMONS_LANG3_ZIP_ENTRY = 60
COMMONS_LANG3_ZIP_MVN_ENTRY = 26


@mock_s3
class S3ClientTest(BaseTest):
    def setUp(self):
        super().setUp()
        # mock_s3 is used to generate expected content
        self.mock_s3 = self.__prepare_s3()
        self.mock_s3.create_bucket(Bucket=MY_BUCKET)
        # s3_client is the client we will test
        self.s3_client = S3Client()

    def tearDown(self):
        bucket = self.mock_s3.Bucket(MY_BUCKET)
        try:
            bucket.objects.all().delete()
            bucket.delete()
        except ValueError:
            pass
        super().tearDown()

    def __prepare_s3(self):
        return boto3.resource('s3')

    def test_get_files(self):
        bucket = self.mock_s3.Bucket(MY_BUCKET)
        bucket.put_object(
            Key="org/foo/bar/1.0/foo-bar-1.0.pom", Body="test content pom"
        )
        bucket.put_object(
            Key="org/foo/bar/1.0/foo-bar-1.0.jar", Body="test content jar"
        )
        bucket.put_object(Key="org/x/y/1.0/x-y-1.0.pom", Body="test content pom")
        bucket.put_object(Key="org/x/y/1.0/x-y-1.0.jar", Body="test content jar")

        (files, _) = self.s3_client.get_files(bucket_name=MY_BUCKET)
        self.assertEqual(4, len(files))
        self.assertIn("org/foo/bar/1.0/foo-bar-1.0.pom", files)
        self.assertIn("org/foo/bar/1.0/foo-bar-1.0.jar", files)
        self.assertIn("org/x/y/1.0/x-y-1.0.pom", files)
        self.assertIn("org/x/y/1.0/x-y-1.0.jar", files)

        (files, _) = self.s3_client.get_files(bucket_name=MY_BUCKET, suffix=".pom")
        self.assertEqual(2, len(files))
        self.assertIn("org/foo/bar/1.0/foo-bar-1.0.pom", files)
        self.assertNotIn("org/foo/bar/1.0/foo-bar-1.0.jar", files)
        self.assertIn("org/x/y/1.0/x-y-1.0.pom", files)
        self.assertNotIn("org/x/y/1.0/x-y-1.0.jar", files)

        (files, _) = self.s3_client.get_files(bucket_name=MY_BUCKET, prefix="org/foo/bar")
        self.assertEqual(2, len(files))
        self.assertIn("org/foo/bar/1.0/foo-bar-1.0.pom", files)
        self.assertIn("org/foo/bar/1.0/foo-bar-1.0.jar", files)
        self.assertNotIn("org/x/y/1.0/x-y-1.0.pom", files)
        self.assertNotIn("org/x/y/1.0/x-y-1.0.jar", files)

        (files, _) = self.s3_client.get_files(
            bucket_name=MY_BUCKET, prefix="org/foo/bar", suffix=".pom"
        )
        self.assertEqual(1, len(files))
        self.assertIn("org/foo/bar/1.0/foo-bar-1.0.pom", files)
        self.assertNotIn("org/foo/bar/1.0/foo-bar-1.0.jar", files)
        self.assertNotIn("org/x/y/1.0/x-y-1.0.pom", files)
        self.assertNotIn("org/x/y/1.0/x-y-1.0.jar", files)

    def test_list_folder_content(self):
        bucket = self.mock_s3.Bucket(MY_BUCKET)
        bucket.put_object(
            Key="index.html", Body="test content html"
        )
        bucket.put_object(
            Key="org/index.html", Body="test content html"
        )
        bucket.put_object(
            Key="org/foo/bar/1.0/foo-bar-1.0.pom", Body="test content pom"
        )
        bucket.put_object(
            Key="org/foo/bar/1.0/foo-bar-1.0.jar", Body="test content jar"
        )
        bucket.put_object(Key="org/x/y/1.0/x-y-1.0.pom", Body="test content pom")
        bucket.put_object(Key="org/x/y/1.0/x-y-1.0.jar", Body="test content jar")

        contents = self.s3_client.list_folder_content(MY_BUCKET, "/")
        self.assertEqual(2, len(contents))
        self.assertIn("index.html", contents)
        self.assertIn("org/", contents)

        contents = self.s3_client.list_folder_content(MY_BUCKET, "org")
        self.assertEqual(3, len(contents))
        self.assertIn("org/foo/", contents)
        self.assertIn("org/x/", contents)
        self.assertIn("org/index.html", contents)

        contents = self.s3_client.list_folder_content(MY_BUCKET, "org/foo")
        self.assertEqual(1, len(contents))
        self.assertIn("org/foo/bar/", contents)

        contents = self.s3_client.list_folder_content(MY_BUCKET, "org/foo/bar")
        self.assertEqual(1, len(contents))
        self.assertIn("org/foo/bar/1.0/", contents)

        contents = self.s3_client.list_folder_content(MY_BUCKET, "org/foo/bar/1.0")
        self.assertEqual(2, len(contents))
        self.assertIn("org/foo/bar/1.0/foo-bar-1.0.pom", contents)
        self.assertIn("org/foo/bar/1.0/foo-bar-1.0.jar", contents)

        contents = self.s3_client.list_folder_content(MY_BUCKET, "org/x/y/1.0")
        self.assertEqual(2, len(contents))
        self.assertIn("org/x/y/1.0/x-y-1.0.pom", contents)
        self.assertIn("org/x/y/1.0/x-y-1.0.jar", contents)

    def test_upload_and_delete_files(self):
        (temp_root, root, all_files) = self.__prepare_files()
        bucket = self.mock_s3.Bucket(MY_BUCKET)
        # test upload existed files with the product. The product will be added to metadata
        self.s3_client.upload_files(
            all_files, targets=[(MY_BUCKET, '')],
            product="apache-commons", root=root
        )

        def content_check(products: List[str], objs: List):
            self.assertEqual(COMMONS_LANG3_ZIP_ENTRY, len(objs))
            for o in objs:
                obj = o.Object()
                if obj.key.endswith(PROD_INFO_SUFFIX):
                    content = str(obj.get()['Body'].read(), 'utf-8')
                    self.assertEqual(
                        set(products),
                        set([f for f in content.split("\n") if f.strip() != ""])
                    )
                else:
                    self.assertNotEqual("", obj.metadata[CHECKSUM_META_KEY])

        objects = list(bucket.objects.all())
        content_check(["apache-commons"], objects)

        # test upload existed files with extra product. The extra product will be added to metadata
        self.s3_client.upload_files(
            all_files, targets=[(MY_BUCKET, '')],
            product="commons-lang3", root=root
        )
        objects = list(bucket.objects.all())
        content_check(set(["apache-commons", "commons-lang3"]), objects)

        # test delete files with one product. The file will not be deleted, but the product will
        # be removed from metadata.
        self.s3_client.delete_files(all_files, target=(MY_BUCKET, ''), product="apache-commons",
                                    root=root)
        objects = list(bucket.objects.all())
        content_check(["commons-lang3"], objects)

        # test delete files with left product. The file will be deleted, because all products
        # have been removed from metadata.
        self.s3_client.delete_files(all_files, target=(MY_BUCKET, ''), product="commons-lang3",
                                    root=root)
        self.assertEqual(0, len(list(bucket.objects.all())))

        shutil.rmtree(temp_root)

    def test_upload_and_delete_with_prefix(self):
        (temp_root, root, all_files) = self.__prepare_files()
        test_files = list(filter(lambda f: f.startswith(root), all_files))

        bucket = self.mock_s3.Bucket(MY_BUCKET)

        self.s3_client.upload_files(
            test_files,
            targets=[(MY_BUCKET, SHORT_TEST_PREFIX)],
            product="apache-commons",
            root=root)
        objects = list(bucket.objects.all())
        self.assertEqual(COMMONS_LANG3_ZIP_MVN_ENTRY * 2, len(objects))
        for obj in objects:
            self.assertTrue(obj.key.startswith(SHORT_TEST_PREFIX))

        self.s3_client.delete_files(
            file_paths=test_files,
            target=(MY_BUCKET, SHORT_TEST_PREFIX),
            product="apache-commons",
            root=root
        )
        objects = list(bucket.objects.all())
        self.assertEqual(0, len(list(bucket.objects.all())))

        shutil.rmtree(temp_root)

    def test_upload_file_with_checksum(self):
        temp_root = os.path.join(self.tempdir, "tmp_upd")
        os.mkdir(temp_root)
        path = "org/foo/bar/1.0"
        os.makedirs(os.path.join(temp_root, path))
        file = os.path.join(temp_root, path, "foo-bar-1.0.txt")
        bucket = self.mock_s3.Bucket(MY_BUCKET)

        content1 = "This is foo bar 1.0 1"
        overwrite_file(file, content1)
        sha1_1 = read_sha1(file)
        self.s3_client.upload_files(
            [file], targets=[(MY_BUCKET, '')],
            product="foo-bar-1.0", root=temp_root
        )
        objects = list(bucket.objects.all())
        self.assertEqual(2, len(objects))
        obj = objects[0].Object()
        self.assertEqual(sha1_1, obj.metadata[CHECKSUM_META_KEY])
        self.assertEqual(
            content1, str(obj.get()["Body"].read(), sys.getdefaultencoding())
        )
        obj = objects[1].Object()
        content = str(obj.get()['Body'].read(), 'utf-8')
        self.assertEqual("foo-bar-1.0", content.strip())

        os.remove(file)

        content2 = "This is foo bar 1.0 2"
        overwrite_file(file, content2)
        sha1_2 = read_sha1(file)
        self.assertNotEqual(sha1_1, sha1_2)
        self.s3_client.upload_files(
            [file], targets=[(MY_BUCKET, '')],
            product="foo-bar-1.0-2", root=temp_root
        )
        objects = list(bucket.objects.all())
        self.assertEqual(2, len(objects))
        obj = objects[0].Object()
        self.assertEqual(sha1_1, obj.metadata[CHECKSUM_META_KEY])
        self.assertEqual(
            content1, str(obj.get()["Body"].read(), sys.getdefaultencoding())
        )
        obj = objects[1].Object()
        content = str(obj.get()['Body'].read(), 'utf-8')
        self.assertEqual("foo-bar-1.0", content.strip())

        shutil.rmtree(temp_root)

    def test_upload_metadata_with_checksum(self):
        temp_root = os.path.join(self.tempdir, "tmp_upd")
        os.mkdir(temp_root)
        path = "org/foo/bar/"
        os.makedirs(os.path.join(temp_root, path))
        file = os.path.join(temp_root, path, "maven-metadata.xml")
        bucket = self.mock_s3.Bucket(MY_BUCKET)

        # First, upload a metadata file
        content1 = """
        <metadata>
            <groupId>org.foo</groupId>
            <artifactId>bar</artifactId>
            <versioning>
                <versions>
                    <version>1.0</version>
                </versions>
            </versioning>
        </metadata>"""
        overwrite_file(file, content1)
        sha1_1 = read_sha1(file)
        self.s3_client.upload_metadatas(
            [file], target=(MY_BUCKET, ''), root=temp_root
        )
        objects = list(bucket.objects.all())
        self.assertEqual(1, len(objects))
        obj = objects[0].Object()
        self.assertEqual(sha1_1, obj.metadata[CHECKSUM_META_KEY])
        self.assertEqual(
            content1, str(obj.get()["Body"].read(), sys.getdefaultencoding())
        )

        # upload this metadata file again with different product
        sha1_1_repeated = read_sha1(file)
        self.assertEqual(sha1_1, sha1_1_repeated)
        self.s3_client.upload_metadatas(
            [file],
            target=(MY_BUCKET, ''),
            root=temp_root,
        )
        objects = list(bucket.objects.all())
        self.assertEqual(1, len(objects))
        obj = objects[0].Object()
        self.assertEqual(sha1_1_repeated, obj.metadata[CHECKSUM_META_KEY])
        self.assertEqual(
            content1, str(obj.get()["Body"].read(), sys.getdefaultencoding())
        )

        os.remove(file)

        # Third, upload the metadata with same file path but different content and product
        content2 = """
        <metadata>
            <groupId>org.foo</groupId>
            <artifactId>bar</artifactId>
            <versioning>
                <versions>
                    <version>1.0</version>
                    <version>1.0.1</version>
                </versions>
            </versioning>
        </metadata>
        """
        overwrite_file(file, content2)
        sha1_2 = read_sha1(file)
        self.assertNotEqual(sha1_1, sha1_2)
        self.s3_client.upload_metadatas(
            [file], target=(MY_BUCKET, ''), root=temp_root
        )
        objects = list(bucket.objects.all())
        self.assertEqual(1, len(objects))
        obj = objects[0].Object()
        self.assertEqual(sha1_2, obj.metadata[CHECKSUM_META_KEY])
        self.assertEqual(
            content2, str(obj.get()["Body"].read(), sys.getdefaultencoding())
        )

        shutil.rmtree(temp_root)

    def test_exists_in_bucket(self):
        bucket = self.mock_s3.Bucket(MY_BUCKET)
        path = "org/foo/bar/1.0/foo-bar-1.0.pom"
        self.assertFalse(self.s3_client.file_exists_in_bucket(MY_BUCKET, path))
        bucket.put_object(
            Key=path, Body="test content pom"
        )
        self.assertTrue(self.s3_client.file_exists_in_bucket(MY_BUCKET, path))

    def test_failed_paths(self):
        (temp_root, root, all_files) = self.__prepare_files()
        shutil.rmtree(root)

        failed_paths = self.s3_client.upload_files(
            all_files, targets=[(MY_BUCKET, '')],
            product="apache-commons", root=temp_root
        )

        self.assertEqual(COMMONS_LANG3_ZIP_MVN_ENTRY, len(failed_paths))

    def test_exists_override_failing(self):
        (temp_root, _, all_files) = self.__prepare_files()
        failed_paths = self.s3_client.upload_files(
            all_files, targets=[(MY_BUCKET, '')],
            product="apache-commons", root=temp_root
        )
        self.assertEqual(0, len(failed_paths))
        sha1 = read_sha1(all_files[0])
        path = all_files[0][len(temp_root) + 1:]

        # Change content to make hash changes
        with open(all_files[0], "w+", encoding="utf-8") as f:
            f.write("changed content")
        sha1_changed = read_sha1(all_files[0])
        self.assertNotEqual(sha1, sha1_changed)
        failed_paths = self.s3_client.upload_files(
            all_files, targets=[(MY_BUCKET, '')],
            product="apache-commons-2", root=temp_root
        )
        bucket = self.mock_s3.Bucket(MY_BUCKET)
        file_obj = bucket.Object(path)
        self.assertEqual(sha1, file_obj.metadata[CHECKSUM_META_KEY])

    def __prepare_files(self):
        test_zip = zipfile.ZipFile(
            os.path.join(INPUTS, "commons-lang3.zip")
        )
        temp_root = os.path.join(self.tempdir, "tmp_zip")
        os.mkdir(temp_root)
        extract_zip_all(test_zip, temp_root)
        root = os.path.join(
            temp_root, "apache-commons-maven-repository/maven-repository"
        )
        all_files = []
        for (directory, _, names) in os.walk(temp_root):
            all_files.extend([os.path.join(directory, n) for n in names])
        return (temp_root, root, all_files)
