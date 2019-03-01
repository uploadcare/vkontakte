#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Tests for vkontakte package.
Requires mock >= 0.7.2.
"""

import os
import sys
import urllib
sys.path.insert(0, os.path.abspath('..'))

import unittest
import mock
import vkontakte
import vkontakte.api

API_ID = 'api_id'
API_SECRET = 'api_secret'

class VkontakteTest(unittest.TestCase):
    def test_api_creation_error(self):
        self.assertRaises(ValueError, lambda: vkontakte.API())

class SignatureTest(unittest.TestCase):
    def test_signature_supports_unicode(self):
        params = {'foo': u'клен'}
        self.assertEqual(
            vkontakte.signature(API_SECRET, params),
            '560b3f1e09ff65167b8dc211604fed2b'
        )

class IterparseTest(unittest.TestCase):
    def test_iterparse(self):
        data = '{"error":{"error_code":8,"error_msg":"Invalid request: this auth method is obsolete, please use oauth. vk.com\/developers","request_params":[{"key":"sig","value":"97aasff03cc81d5db25de67893e207"},{"key":"uids","value":"1,2"},{"key":"timestamp","value":"1355095295"},{"key":"v","value":"3.0"},{"key":"fields","value":"education"},{"key":"format","value":"JSON"},{"key":"random","value":"937530097"},{"key":"method","value":"getProfiles"},{"key":"api_id","value":"3267523"}]}}{"error":{"error_code":8,"error_msg":"Invalid request: this auth method is obsolete, please use oauth. vk.com\/developers","request_params":[{"key":"sig","value":"97aasff03cc81d5db25de67893e207"},{"key":"uids","value":"1,2"},{"key":"timestamp","value":"1355095295"},{"key":"v","value":"3.0"},{"key":"fields","value":"education"},{"key":"format","value":"JSON"},{"key":"random","value":"937530097"},{"key":"method","value":"getProfiles"},{"key":"api_id","value":"3267523"}]}}{"response":[{"uid":1,"first_name":"Павел","last_name":"Дуров","university":1,"university_name":"СПбГУ","faculty":15,"faculty_name":"Филологический","graduation":2006},{"uid":2,"first_name":"Александра","last_name":"Владимирова"}]}'
        parses = list(vkontakte.api._json_iterparse(data))
        self.assertEqual(len(parses),  3)
        assert "error" in parses[0]
        assert "error" in parses[1]
        self.assertEqual(parses[2]["response"][0]["first_name"], u"Павел")

    def test_iterparse_edge(self):
        data = '{"error": {"}{": "foo"}}{"foo":"bar"}'
        parses = list(vkontakte.api._json_iterparse(data))
        self.assertEqual(parses[0]["error"]["}{"], "foo")
        self.assertEqual(parses[1]["foo"], "bar")



class VkontakteMagicTest(unittest.TestCase):

    def setUp(self):
        self.api = vkontakte.API(API_ID, API_SECRET)

    @mock.patch('vkontakte.api._API._get')
    def test_basic(self, _get):
        _get.return_value = '123'
        time = self.api.getServerTime()
        self.assertEqual(time, '123')
        _get.assert_called_once_with('getServerTime')

    @mock.patch('vkontakte.api._API._get')
    def test_with_arguments(self, _get):
        _get.return_value = [{'last_name': u'Дуров'}]
        res = self.api.getProfiles(uids='1,2', fields='education')
        self.assertEqual(res, _get.return_value)
        _get.assert_called_once_with('getProfiles', uids='1,2', fields='education')

    @mock.patch('vkontakte.api._API._get')
    def test_with_arguments_get(self, _get):
        _get.return_value = [{'last_name': u'Дуров'}]
        res = self.api.get('getProfiles', uids='1,2', fields='education')
        self.assertEqual(res, _get.return_value)
        _get.assert_called_once_with('getProfiles', vkontakte.api.DEFAULT_TIMEOUT, uids='1,2', fields='education')

    @mock.patch('vkontakte.http.post')
    def test_timeout(self, post):
        post.return_value = 200, '{"response":123}'
        api = vkontakte.API(API_ID, API_SECRET, timeout=5)
        res = api.getServerTime()
        self.assertEqual(res, 123)
        self.assertEqual(post.call_args[0][3], 5)

    @mock.patch('vkontakte.api._API._get')
    def test_magic(self, _get):
        for method in vkontakte.api.COMPLEX_METHODS:
            _get.return_value = None
            res = getattr(self.api, method).test()
            self.assertEqual(res, None)
            _get.assert_called_once_with('%s.test' % method)
            _get.reset_mock()

    @mock.patch('vkontakte.api._API._get')
    def test_magic_get(self, _get):
        _get.return_value = 'foo'
        res = self.api.friends.get(uid=642177)
        self.assertEqual(res, 'foo')
        _get.assert_called_once_with('friends.get', uid=642177)

    @mock.patch('vkontakte.http.post')
    def test_urlencode_bug(self, post):
        post.return_value = 200, '{"response":123}'
        res = self.api.search(q=u'клен')
        self.assertEqual(res, 123)

    @mock.patch('vkontakte.http.post')
    def test_valid_quoted_json(self, post):
        post.return_value = 200, '{"response": 123}'
        self.api.ads.getStat(data={'type': '1', 'id': 1})
        posted_data = urllib.unquote(post.call_args[0][1])
        self.assertTrue('data={"type":+"1",+"id":+1}' in posted_data, posted_data)

    @mock.patch('vkontakte.http.post')
    def test_unicode_decode_error(self, post):
        post.return_value = 200, '{"response":[35,{"cid":195478,"uid":223297741,"from_id":223297741,"date":1386616969,"text":"[id152534333|\xd0\x90\xd0\xbd\xd0\xb4\xd1\x80\xd0\xb5\xd0\xb9], \xd0\xb4\xd0\xbb\xd1\x8f \xd1\x81\xd1\x82\xd0\xb0\xd1\x82\xd0\xb8\xd1\x81\xd1\x82\xd0\xb8\xd0\xba\xd0\xb8 \xd0\xb2 \xd1\x84\xd1\x81\xd0\xb1","likes":{"count":0,"user_likes":0,"can_like":1},"reply_to_uid":152534333,"reply_to_cid":195368},{"cid":195370,"uid":225734427,"from_id":225734427,"date":1386606029,"text":"[id14808949|\xd0\x9b\xd0\xb8\xd0\xbb\xd0\xb8\xd1\x8f], \xd0\xb2 \xd0\xbc\xd0\xb0\xd1\x80\xd1\x81 \xd1\x8f \xd0\xb2\xd0\xb5\xd1\x80\xd1\x8e!)))))) http:\\/\\/ru.wikipedia.org\\/wiki\\/\xd0\x9a\xd0\xbe\xd0\xbb\xd0\xbe\xd0\xbd\xd0\xb8\xd0\xb7\xd0\xb0\xd1\x86\xd0\xb8\xd1\x8f_\xd0\x9c\xd0\xb0\xd1\x80\xd1\x81\xd0\xb0 http:\\/\\/ru.wikipedia.org\\/wiki\\/\xca\xee\xeb\xee\xed\xe8\xe7\xe0\xf6\xe8\xff_\xcc\xe0\xf0\xf1\xe0","likes":{"count":3,"user_likes":0,"can_like":1},"reply_to_uid":14808949,"reply_to_cid":195359},{"cid":195368,"uid":152534333,"from_id":152534333,"date":1386605970,"text":"\xd0\x9e\xd0\xb4\xd0\xb8\xd0\xbd \xd0\xb2\xd0\xbe\xd0\xbf\xd1\x80\xd0\xbe\xd1\x81: \xd0\xb7\xd0\xb0\xd1\x87\xd0\xb5\xd0\xbc?","likes":{"count":0,"user_likes":0,"can_like":1}},{"cid":195359,"uid":14808949,"from_id":14808949,"date":1386605354,"text":"[id225734427|\xd0\xa0\xd1\x83\xd1\x81\xd1\x82\xd0\xb0\xd0\xbc], \xd1\x81\xd0\xb0\xd0\xbc \xd0\xb2 \xd1\x8d\xd1\x82\xd0\xbe \xd0\xb2\xd0\xb5\xd1\x80\xd0\xb8\xd1\x88\xd1\x8c ?","likes":{"count":0,"user_likes":0,"can_like":1},"reply_to_uid":225734427,"reply_to_cid":195358},{"cid":195358,"uid":225734427,"from_id":225734427,"date":1386605334,"text":"[id14808949|\xd0\x9b\xd0\xb8\xd0\xbb\xd0\xb8\xd1\x8f], \xd0\xbf\xd1\x83\xd1\x81\xd1\x82\xd1\x8c \xd0\xbe\xd0\xbf\xd1\x80\xd0\xb5\xd0\xb4\xd0\xb5\xd0\xbb\xd1\x8f\xd1\x8e\xd1\x82 \xd0\xba\xd0\xb0\xd0\xba \xd1\x85\xd0\xbe\xd1\x82\xd1\x8f\xd1\x82. \xd1\x85\xd0\xbe\xd1\x87\xd0\xb5\xd1\x82 \xd0\xb1\xd1\x8b\xd1\x82\xd1\x8c \xd1\x87\xd0\xb5\xd0\xbb\xd0\xbe\xd0\xb2\xd0\xb5\xd0\xba - \\"\xd0\xbc\xd0\xb0\xd1\x80\xd1\x81\xd0\xb8\xd0\xb0\xd0\xbd\xd0\xb8\xd0\xbd\xd0\xbe\xd0\xbc\\" \xd0\xbf\xd1\x83\xd1\x81\xd1\x82\xd1\x8c \xd0\xb1\xd1\x83\xd0\xb4\xd0\xb5\xd1\x82. \xd1\x83 \xd0\xba\xd0\xb0\xd0\xb6\xd0\xb4\xd0\xbe\xd0\xb3\xd0\xbe \xd1\x81\xd0\xb2\xd0\xbe\xd0\xb8 \xd0\xbc\xd0\xbe\xd0\xb7\xd0\xb3\xd0\xb8 (\xd0\xb4\xd0\xb0\xd0\xb6\xd0\xb5 \xd0\xb5\xd1\x81\xd0\xbb\xd0\xb8 \xd0\xbe\xd0\xbd\xd0\xb8 \xd0\xbf\xd1\x83\xd1\x81\xd1\x82\xd1\x8b\xd0\xb5))) \xd0\xb2 \xd0\xba\xd0\xbe\xd0\xbd\xd1\x86\xd0\xb5 \xd0\xba\xd0\xbe\xd0\xbd\xd1\x86\xd0\xbe\xd0\xb2 \xd0\xbc\xd0\xb0\xd1\x80\xd1\x81 \xd0\xb2\xd0\xb5\xd0\xb4\xd1\x8c \xd0\xb1\xd1\x83\xd0\xb4\xd1\x83\xd1\x82 \xd0\xba\xd0\xbe\xd0\xb3\xd0\xb4\xd0\xb0-\xd0\xbd\xd0\xb8\xd0\xb1\xd1\x83\xd0\xb4\xd1\x8c \xd0\xba\xd0\xbe\xd0\xbb\xd0\xbe\xd0\xbd\xd0\xb8\xd0\xb7\xd0\xb8\xd1\x80\xd0\xbe\xd0\xb2\xd0\xb0\xd1\x82\xd1\x8c))))","likes":{"count":0,"user_likes":0,"can_like":1},"reply_to_uid":14808949,"reply_to_cid":195340},{"cid":195354,"uid":231583480,"from_id":231583480,"date":1386605275,"text":"https:\\/\\/docs.google.com\\/forms\\/d\\/19ZSLp3TGSIWtW_zYfYelpiyZ7eVfPrw_TSQidEhBojg\\/viewform","likes":{"count":0,"user_likes":0,"can_like":1}},{"cid":195348,"uid":90729922,"from_id":90729922,"date":1386604909,"text":"\xd0\xa0\xd0\xb0\xd0\xb7\xd1\x80\xd0\xb0\xd0\xb1\xd0\xbe\xd1\x82\xd0\xb0\xd0\xbb \xd0\xb8\xd0\xbd\xd1\x81\xd1\x82\xd0\xb8\xd1\x82\xd1\x83\xd1\x82 \xd0\xb3\xd0\xbb\xd1\x83\xd0\xb1\xd0\xbe\xd0\xba\xd0\xbe - \xd0\xbd\xd0\xb0\xd1\x83\xd1\x87\xd0\xbd\xd1\x8b\xd0\xb9 \xd1\x82\xd1\x80\xd1\x83\xd0\xb4: \\"\xd0\x9e \xd0\xb2\xd0\xbb\xd0\xb8\xd1\x8f\xd0\xbd\xd0\xb8\xd0\xb8 \xd0\xba\xd0\xbe\xd0\xbc\xd0\xb0\xd1\x80\xd0\xbe\xd0\xb2 \xd0\xbd\xd0\xb0 \xd0\xbc\xd1\x8b\xd1\x87\xd0\xb0\xd0\xbd\xd0\xb8\xd0\xb5 \xd0\xba\xd0\xbe\xd1\x80\xd0\xbe\xd0\xb2!\\"","likes":{"count":0,"user_likes":0,"can_like":1}},{"cid":195342,"uid":1976765,"from_id":1976765,"date":1386604786,"text":"[id197770104|\xd0\x90\xd0\xbb\xd0\xb5\xd0\xba\xd1\x81\xd0\xb5\xd0\xb9], \xd0\xb0 \xd0\xb5\xd1\x89\xd0\xb5 \xd0\xb5\xd0\xb2\xd1\x80\xd0\xb5\xd0\xb8 \xd0\xbf\xd1\x80\xd0\xb8\xd0\xb4\xd1\x83\xd0\xbc\xd0\xb0\xd0\xbb\xd0\xb8 \xd1\x82\xd0\xb5\xd0\xbe\xd1\x80\xd0\xb8\xd1\x8e \xd0\xbe\xd1\x82\xd0\xbd\xd0\xbe\xd1\x81\xd0\xb8\xd1\x82\xd0\xb5\xd0\xbb\xd1\x8c\xd0\xbd\xd0\xbe\xd1\x81\xd1\x82\xd0\xb8. \xd0\xba\xd0\xb0\xd0\xba \xd0\xbb\xd0\xb5\xd1\x82\xd0\xb0\xd1\x82\xd1\x8c \xd0\xb2 \xd0\xba\xd0\xbe\xd1\x81\xd0\xbc\xd0\xbe\xd1\x81. \xd0\xb4\xd0\xb0\xd0\xbb\xd0\xb8 \xd0\xbd\xd0\xb0\xd1\x87\xd0\xb0\xd0\xbb\xd0\xbe \xd0\xba\xd0\xb2\xd0\xb0\xd0\xbd\xd1\x82\xd0\xbe\xd0\xb2\xd0\xbe\xd0\xb9 \xd1\x84\xd0\xb8\xd0\xb7\xd0\xb8\xd0\xba\xd0\xb5 \xd0\xb8 \xd0\xb5\xd1\x89\xd0\xb5 \xd0\xbc\xd0\xbd\xd0\xbe\xd0\xb3\xd0\xbe \xd1\x87\xd0\xb5\xd0\xb3\xd0\xbe. \xd0\xba\xd0\xbe\xd0\xbd\xd0\xb5\xd1\x87\xd0\xbd\xd0\xbe. \xd0\xb8\xd0\xbc \xd1\x81\xd1\x82\xd1\x8b\xd0\xb4\xd0\xbd\xd0\xbe \xd0\xb7\xd0\xb0 \xd1\x82\xd0\xbe, \xd1\x87\xd1\x82\xd0\xbe \xd0\xbe\xd0\xbd\xd0\xb8 \xd0\xb5\xd0\xb2\xd1\x80\xd0\xb5\xd0\xb8. \xd0\xbf\xd1\x80\xd0\xbe\xd1\x81\xd1\x82\xd0\xbe \xd0\xb1\xd1\x80\xd0\xb1\xd1\x80\xd0\xb1\xd1\x80 \xd0\xba\xd0\xb0\xd0\xba \xd1\x81\xd1\x82\xd1\x8b\xd0\xb4\xd0\xbd\xd0\xbe","likes":{"count":1,"user_likes":0,"can_like":1},"reply_to_uid":197770104,"reply_to_cid":195316},{"cid":195340,"uid":14808949,"from_id":14808949,"date":1386604639,"text":"[id225734427|\xd0\xa0\xd1\x83\xd1\x81\xd1\x82\xd0\xb0\xd0\xbc], \xd0\x92\xd0\xb0\xd1\x88\xd0\xb0 \xd0\xbf\xd0\xbe\xd0\xb7\xd0\xb8\xd1\x86\xd0\xb8\xd1\x8f \xd0\xbf\xd0\xbe\xd0\xbd\xd1\x8f\xd1\x82\xd0\xbd\xd0\xb0. \xd0\xb5\xd1\x81\xd1\x82\xd1\x8c \xd1\x82\xd0\xb5 \xd0\xba\xd1\x82\xd0\xbe \xd1\x81\xd0\xb2\xd0\xbe\xd1\x8e \xd0\xbd\xd0\xb0\xd1\x86\xd0\xb8\xd0\xbe\xd0\xbd\xd0\xb0\xd0\xbb\xd1\x8c\xd0\xbd\xd0\xbe\xd1\x81\xd1\x82\xd1\x8c \xd0\xbe\xd0\xbf\xd1\x80\xd0\xb5\xd0\xb4\xd0\xb5\xd0\xbb\xd1\x8f\xd1\x8e\xd1\x82 \xd0\xb8 \xd0\xbf\xd0\xbe \xd0\xbe\xd1\x82\xd1\x86\xd1\x83 \xd0\xb8 \xd0\xbf\xd0\xbe \xd0\xbc\xd0\xb0\xd0\xbc\xd0\xb5. \xd0\x90 \xd0\xb5\xd1\x81\xd1\x82\xd1\x8c \xd1\x82\xd0\xb5, \xd0\xba\xd1\x82\xd0\xbe \xd1\x8d\xd1\x82\xd0\xbe\xd0\xbc\xd1\x83 \xd0\xbf\xd1\x80\xd0\xb0\xd0\xb2\xd0\xb8\xd0\xbb\xd1\x83 \xd0\xbd\xd0\xb5 \xd1\x81\xd0\xbb\xd0\xb5\xd0\xb4\xd1\x83\xd0\xb5\xd1\x82. \xd1\x82\xd0\xb0\xd0\xba \xd1\x87\xd1\x82\xd0\xbe \xd1\x8d\xd1\x82\xd0\xb0 \xd0\xb8\xd0\xbd\xd0\xb8\xd1\x86\xd0\xb8\xd0\xb0\xd1\x82\xd0\xb8\xd0\xb2\xd0\xb0 \xd0\xbd\xd0\xb0 \xd0\xbc\xd0\xbe\xd0\xb9 \xd0\xb2\xd0\xb7\xd0\xb3\xd0\xbb\xd1\x8f\xd0\xb4 \xd0\xbd\xd0\xb5 \xd0\xb1\xd1\x83\xd0\xb4\xd0\xb5\xd1\x82 \xd0\xbe\xd1\x82\xd1\x80\xd0\xb0\xd0\xb6\xd0\xb0\xd1\x82\xd1\x8c \xd0\xb4\xd0\xb5\xd0\xb9\xd1\x81\xd1\x82\xd0\xb2\xd0\xb8\xd1\x82\xd0\xb5\xd0\xbb\xd1\x8c\xd0\xbd\xd0\xbe\xd1\x81\xd1\x82\xd0\xb8.","likes":{"count":0,"user_likes":0,"can_like":1},"reply_to_uid":225734427,"reply_to_cid":195339},{"cid":195339,"uid":225734427,"from_id":225734427,"date":1386604440,"text":"[id14808949|\xd0\x9b\xd0\xb8\xd0\xbb\xd0\xb8\xd1\x8f], \xd1\x83 \xd1\x87\xd0\xb5\xd0\xbb\xd0\xbe\xd0\xb2\xd0\xb5\xd0\xba\xd0\xb0 \xd0\xbd\xd0\xb5 \xd0\xbc\xd0\xbe\xd0\xb6\xd0\xb5\xd1\x82 \xd0\xb1\xd1\x8b\xd1\x82\xd1\x8c \xd0\xb4\xd0\xb2\xd1\x83\xd1\x85 \xd0\xbd\xd0\xb0\xd1\x86\xd0\xb8\xd0\xbe\xd0\xbd\xd0\xb0\xd0\xbb\xd1\x8c\xd0\xbd\xd0\xbe\xd1\x81\xd1\x82\xd0\xb5\xd0\xb9. \xd0\xbc\xd0\xbe\xd0\xb6\xd0\xbd\xd0\xbe (\xd0\xbd\xd1\x83\xd0\xb6\xd0\xbd\xd0\xbe!) \xd1\x83\xd0\xb2\xd0\xb0\xd0\xb6\xd0\xb0\xd1\x82\xd1\x8c \xd0\xb4\xd1\x80\xd1\x83\xd0\xb3\xd0\xb8\xd0\xb5 \xd0\xbd\xd0\xb0\xd1\x80\xd0\xbe\xd0\xb4\xd1\x8b, \xd0\xbd\xd0\xbe \xd0\xbd\xd0\xb0\xd0\xb4\xd0\xbe \xd0\xb1\xd1\x8b\xd1\x82\xd1\x8c \xd0\xba\xd0\xb5\xd0\xbc-\xd1\x82\xd0\xbe \xd0\xb0 \xd0\xbd\xd0\xb5 \xd0\xb2\xd1\x81\xd0\xb5\xd0\xbc)) \xd0\xbd\xd0\xb5\xd0\xbb\xd1\x8c\xd0\xb7\xd1\x8f \xd0\xb1\xd1\x8b\xd1\x82\xd1\x8c \xd1\x80\xd1\x83\xd1\x81\xd1\x81\xd0\xba\xd0\xbe-\xd1\x82\xd0\xb0\xd1\x82\xd0\xb0\xd1\x80\xd0\xb8\xd0\xbd\xd0\xbe\xd0\xbc, \xd0\xb5\xd0\xb2\xd1\x80\xd0\xb5\xd0\xb5-\xd0\xbf\xd0\xbe\xd0\xbb\xd1\x8f\xd0\xba\xd0\xbe\xd0\xbc \xd0\xb8\xd0\xbb\xd0\xb8 \xd0\xbc\xd1\x83\xd1\x81\xd1\x83\xd0\xbb\xd1\x8c\xd0\xbc\xd0\xb0\xd0\xbd\xd0\xbe-\xd0\xbf\xd1\x80\xd0\xb0\xd0\xb2\xd0\xbe\xd1\x81\xd0\xbb\xd0\xb0\xd0\xb2\xd0\xbd\xd1\x8b\xd0\xbc)))) \xd0\xb2\xd1\x81\xd0\xb5 \xd0\xbe\xd1\x81\xd1\x82\xd0\xb0\xd0\xbb\xd1\x8c\xd0\xbd\xd0\xbe\xd0\xb5 \xd0\x94\xd0\x95\xd0\x9c\xd0\x90\xd0\x93\xd0\x9e\xd0\x93\xd0\x98\xd0\xaf \xd1\x87\xd1\x82\xd0\xbe-\xd0\xb1\xd1\x8b \xd0\xbf\xd1\x80\xd0\xb8\xd0\xba\xd1\x80\xd1\x8b\xd1\x82\xd1\x8c \xd0\xbe\xd1\x82\xd1\x81\xd1\x83\xd1\x82\xd1\x81\xd1\x82\xd0\xb2\xd0\xb8\xd0\xb5 \xd0\xbb\xd1\x8e\xd0\xb1\xd0\xbe\xd0\xb9 \xd0\xba\xd1\x83\xd0\xbb\xd1\x8c\xd1\x82\xd1\x83\xd1\x80\xd0\xbd\xd0\xbe\xd0\xb9 \xd0\xbe\xd1\x81\xd0\xbd\xd0\xbe\xd0\xb2\xd1\x8b \xd0\xb8\xd0\xbb\xd0\xb8 \xd1\x85\xd0\xb8\xd1\x82\xd1\x80\xd0\xb0\xd1\x8f \xd0\xbf\xd0\xbe\xd0\xb7\xd0\xb8\xd1\x86\xd0\xb8\xd1\x8f (\xd0\xb2 \xd1\x80\xd0\xbe\xd1\x81\xd1\x81\xd0\xb8\xd1\x8f - \xd1\x8f \xd1\x80\xd1\x83\xd1\x81\xd1\x81\xd0\xba\xd0\xb8\xd0\xb9 \xd0\xb2 \xd0\xb8\xd0\xb7\xd1\x80\xd0\xb0\xd0\xb8\xd0\xbb\xd0\xb5 - \xd1\x8f \xd0\xb5\xd0\xb2\xd1\x80\xd0\xb5\xd0\xb9))) \xd0\xb4\xd0\xb5\xd1\x82\xd0\xb8 \xd0\xb4\xd0\xbe\xd0\xbb\xd0\xb6\xd0\xbd\xd1\x8b \xd1\x81\xd0\xb4\xd0\xb5\xd0\xbb\xd0\xb0\xd1\x82\xd1\x8c \xd0\xb2\xd1\x8b\xd0\xb1\xd0\xbe\xd1\x80 \xd0\xba\xd0\xbe\xd0\xb3\xd0\xb4\xd0\xb0 \xd0\xbf\xd0\xbe\xd0\xb2\xd0\xb7\xd1\x80\xd0\xbe\xd1\x81\xd0\xbb\xd0\xb5\xd1\x8e\xd1\x82","likes":{"count":8,"user_likes":0,"can_like":1},"reply_to_uid":14808949,"reply_to_cid":195326},{"cid":195326,"uid":14808949,"from_id":14808949,"date":1386603984,"text":"[id225734427|\xd0\xa0\xd1\x83\xd1\x81\xd1\x82\xd0\xb0\xd0\xbc], \xd1\x8f \xd0\xbe \xd0\xb4\xd0\xb5\xd1\x82\xd1\x8f\xd1\x85 \xd0\xb2 \xd1\x81\xd0\xbc\xd0\xb5\xd1\x88\xd0\xb0\xd0\xbd\xd0\xbd\xd1\x8b\xd1\x85 \xd0\xb1\xd1\x80\xd0\xb0\xd0\xba\xd0\xb0\xd1\x85.","likes":{"count":0,"user_likes":0,"can_like":1},"reply_to_uid":225734427,"reply_to_cid":195323},{"cid":195323,"uid":225734427,"from_id":225734427,"date":1386603941,"text":"[id14808949|\xd0\x9b\xd0\xb8\xd0\xbb\xd0\xb8\xd1\x8f], \xd0\xb5\xd1\x81\xd0\xbb\xd0\xb8 \xd1\x82\xd0\xb0\xd0\xba\xd0\xbe\xd0\xb9 \xd0\xb2\xd0\xbe\xd0\xbf\xd1\x80\xd0\xbe\xd1\x81 \xd0\xb7\xd0\xb0\xd0\xb4\xd0\xb0\xd0\xb5\xd1\x82\xd1\x81\xd1\x8f \xd1\x82\xd0\xbe \xd0\xbd\xd0\xb0\xd1\x86\xd0\xb8\xd0\xbe\xd0\xbd\xd0\xb0\xd0\xbb\xd1\x8c\xd0\xbd\xd0\xbe\xd1\x81\xd1\x82\xd1\x8c \xd0\xbe\xd0\xb4\xd0\xbd\xd0\xb0 - \xd0\xbc\xd0\xb0\xd0\xbd\xd0\xba\xd1\x83\xd1\x80\xd1\x82","likes":{"count":0,"user_likes":0,"can_like":1},"reply_to_uid":14808949,"reply_to_cid":195314},{"cid":195319,"uid":167496147,"from_id":167496147,"date":1386603872,"text":"[id165400079|\xd0\x90\xd1\x80\xd1\x82\xd1\x91\xd0\xbc], \xd1\x8f \xd0\xbd\xd0\xb5 \xd0\xbf\xd1\x80\xd0\xbe \xd0\xb3\xd1\x80\xd1\x83\xd0\xb4\xd1\x8c, \xd0\xb1\xd0\xb5\xd1\x80\xd0\xb8 \xd0\xbd\xd0\xb8\xd0\xb6\xd0\xb5 )))","likes":{"count":0,"user_likes":0,"can_like":1},"reply_to_uid":165400079,"reply_to_cid":195299},{"cid":195318,"uid":209113652,"from_id":209113652,"date":1386603848,"text":"\xd0\xa1\xd0\xbb\xd0\xb0\xd0\xb2\xd0\xb0 \xd0\x9f\xd0\xb5\xd1\x82\xd0\xb5\xd1\x80\xd0\xb1\xd1\x83\xd1\x80\xd0\xb3\xd1\x83!!!","likes":{"count":0,"user_likes":0,"can_like":1}},{"cid":195317,"uid":207803816,"from_id":207803816,"date":1386603803,"text":"\xd0\x98 \xd1\x81\xd1\x82\xd0\xb0\xd1\x82\xd0\xbe\xd1\x82\xd0\xb4\xd0\xb5\xd0\xbb \xd1\x80\xd0\xb0\xd1\x81\xd1\x88\xd0\xb8\xd1\x80\xd0\xb8\xd0\xbc, \xd0\xb8 \xd0\xbd\xd0\xbe\xd0\xb2\xd1\x8b\xd0\xb5 \xd0\xb1\xd0\xbb\xd0\xb0\xd0\xbd\xd0\xba\xd0\xb8 \xd0\xbd\xd0\xb0\xd0\xbf\xd0\xb5\xd1\x87\xd0\xb0\xd1\x82\xd0\xb0\xd0\xb5\xd0\xbc, \xd0\xb8 \xd0\xbd\xd0\xbe\xd0\xb2\xd1\x8b\xd0\xb5 \xd0\xba\xd0\xbe\xd0\xbc\xd0\xbf\xd1\x8c\xd1\x8e\xd1\x82\xd0\xb5\xd1\x80\xd0\xbd\xd1\x8b\xd0\xb5 \xd0\xbf\xd1\x80\xd0\xbe\xd0\xb3\xd0\xb8 \xd0\xb7\xd0\xb0\xd0\xba\xd1\x83\xd0\xbf\xd0\xb8\xd0\xbc... \xd1\x87\xd0\xb8\xd1\x81\xd1\x82\xd1\x8b\xd0\xb9 \xd1\x80\xd0\xb0\xd1\x81\xd0\xbf\xd0\xb8\xd0\xbb \xd0\xb8 \xd0\xbd\xd0\xb8\xd0\xba\xd0\xb0\xd0\xba\xd0\xbe\xd0\xb3\xd0\xbe \xd0\xbd\xd0\xb0\xd1\x86\xd0\xb8\xd0\xbe\xd0\xbd\xd0\xb0\xd0\xbb\xd0\xb8\xd0\xb7\xd0\xbc\xd0\xb0.<br>\xd0\x90 \xd0\xbf\xd0\xb0\xd1\x82\xd1\x80\xd0\xb8\xd0\xbe\xd1\x82\xd0\xb0\xd0\xbc \xd0\xbb\xd0\xb8\xd1\x88\xd1\x8c \xd0\xb1\xd1\x8b \xd0\xbf\xd0\xbe\xd0\xb3\xd1\x83\xd0\xbd\xd0\xb4\xd0\xb5\xd1\x82\xd1\x8c \xd0\xbe \xd1\x81\xd0\xb2\xd0\xbe\xd1\x91\xd0\xbc, \xd0\xbe \xd0\xb4\xd0\xb5\xd0\xb2\xd0\xb8\xd1\x87\xd1\x8c\xd0\xb5\xd0\xbc.","likes":{"count":0,"user_likes":0,"can_like":1}},{"cid":195316,"uid":197770104,"from_id":197770104,"date":1386603710,"text":"\xd1\x8d\xd1\x82\xd0\xbe \xd0\xbf\xd1\x80\xd0\xb8\xd0\xb4\xd1\x83\xd0\xbc\xd0\xb0\xd0\xbb\xd0\xb8 \xd0\xb5\xd0\xb2\xd1\x80\xd0\xb5\xd0\xb8  \xd0\xb8\xd0\xbc \xd1\x81\xd1\x82\xd1\x8b\xd0\xb4\xd0\xbd\xd0\xbe \xd1\x81\xd0\xba\xd0\xb0\xd0\xb7\xd0\xb0\xd1\x82\xd1\x8c \xd1\x87\xd1\x82\xd0\xbe \xd0\xbe\xd0\xbd\xd0\xb8 \xd0\xb5\xd0\xb2\xd1\x80\xd0\xb5\xd0\xb8 ))","likes":{"count":1,"user_likes":0,"can_like":1}},{"cid":195314,"uid":14808949,"from_id":14808949,"date":1386603606,"text":"[id225734427|\xd0\xa0\xd1\x83\xd1\x81\xd1\x82\xd0\xb0\xd0\xbc], \xd0\xbd\xd0\xb0\xd1\x86\xd0\xb8\xd0\xbe\xd0\xbd\xd0\xb0\xd0\xbb\xd1\x8c\xd0\xbd\xd0\xbe\xd1\x81\xd1\x82\xd1\x8c \xd0\xbd\xd0\xb0\xd1\x86\xd0\xb8\xd0\xbe\xd0\xbd\xd0\xb0\xd0\xbb\xd1\x8c\xd0\xbd\xd0\xbe\xd1\x81\xd1\x82\xd1\x8c\xd1\x8e, \xd0\xb0 \xd0\xba\xd0\xb0\xd0\xba \xd0\xb5\xd1\x91 \xd0\xbe\xd0\xbf\xd1\x80\xd0\xb5\xd0\xb4\xd0\xb5\xd0\xbb\xd1\x8f\xd1\x82\xd1\x8c?","likes":{"count":1,"user_likes":0,"can_like":1},"reply_to_uid":225734427,"reply_to_cid":195310},{"cid":195313,"uid":213252379,"from_id":213252379,"date":1386603572,"text":"\xd0\xa5\xd0\xb0\xd0\xba\xd0\xb8\xd0\xbc\xd0\xbe\xd0\xb2, \xd0\xbd\xd0\xb5 \xd1\x83 \xd0\xb2\xd1\x81\xd0\xb5\xd1\x85 \xd0\xbd\xd0\xb0\xd1\x86\xd0\xb8\xd0\xbe\xd0\xbd\xd0\xb0\xd0\xbb\xd1\x8c\xd0\xbd\xd0\xbe\xd1\x81\xd1\x82\xd1\x8c \xd0\xbd\xd0\xb0 \xd0\xbb\xd0\xb1\xd1\x83 \xd0\xbd\xd0\xb0\xd0\xbf\xd0\xb8\xd1\x81\xd0\xb0\xd0\xbd\xd0\xb0.","likes":{"count":0,"user_likes":0,"can_like":1},"reply_to_uid":225734427,"reply_to_cid":195310},{"cid":195312,"uid":144124676,"from_id":144124676,"date":1386603564,"text":"\xd0\xa3\xd0\xb6\xd0\xb5 \xd0\xbd\xd0\xb5 \xd0\xb7\xd0\xbd\xd0\xb0\xd1\x8e\xd1\x82 \xd0\xbd\xd0\xb0 \xd0\xba\xd0\xb0\xd0\xba\xd0\xbe\xd0\xb9 \xd1\x83\xd1\x87\xd0\xb5\xd1\x82 \xd0\xbd\xd0\xb0\xd1\x80\xd0\xbe\xd0\xb4 \xd0\xbf\xd0\xbe\xd1\x81\xd1\x82\xd0\xb0\xd0\xb2\xd0\xb8\xd1\x82\xd1\x8c!!!  \xd0\x98\xd0\xbd\xd1\x81\xd1\x82\xd0\xb8\xd1\x82\xd1\x83\xd1\x82 \xd0\xbf\xd1\x80\xd0\xbe\xd0\xbf\xd0\xb8\xd1\x81\xd0\xba\xd0\xbc \xd1\x82\xd0\xbe\xd0\xb6\xd0\xb5 \xd0\xb2\xd1\x80\xd0\xbe\xd0\xb4\xd0\xb5 \xd0\xba\xd0\xb0\xd0\xba \xd0\xbe\xd1\x82\xd0\xbc\xd0\xbd\xd0\xb5\xd0\xbd, \xd0\xbd\xd0\xbe \xd0\xb7\xd0\xb0 \xd0\xbf\xd1\x80\xd0\xbe\xd0\xb6\xd0\xb8\xd0\xb2\xd0\xb0\xd0\xbd\xd0\xb8\xd0\xb5 \xd0\xb1\xd0\xb5\xd0\xb7 \xd1\x80\xd0\xb5\xd0\xb3\xd0\xb8\xd1\x81\xd1\x82\xd1\x80\xd0\xb0\xd1\x86\xd0\xb8\xd0\xb8 \xd0\xbf\xd0\xbe \xd0\xbc\\/\xd0\xb6\xd0\xb8\xd1\x82\xd0\xb5\xd0\xbb\xd1\x8c\xd1\x81\xd1\x82\xd0\xb2\xd0\xb0 \xd0\xb8\xd0\xbb\xd0\xb8 \xd0\xbc\\/\xd0\xbf\xd1\x80\xd0\xb5\xd0\xb1\xd1\x8b\xd0\xb2\xd0\xb0\xd0\xbd\xd0\xb8\xd1\x8f \xd0\xb7\xd0\xb0\xd0\xbf\xd1\x80\xd0\xbe\xd1\x81\xd1\x82\xd0\xbe \xd1\x81\xd1\x85\xd0\xbb\xd0\xbe\xd0\xbf\xd0\xbe\xd1\x87\xd0\xb5\xd1\x88\xd1\x8c \xd0\xb0\xd0\xb4\xd0\xbc\xd0\xb8\xd0\xbd\xd0\xb8\xd1\x81\xd1\x82\xd1\x80\xd0\xb0\xd1\x82\xd0\xb8\xd0\xb2\xd0\xbd\xd1\x8b\xd0\xb9 \xd1\x88\xd1\x82\xd1\x80\xd0\xb0\xd1\x84 \xd0\xb2 \xd1\x80-\xd1\x80\xd0\xb5 1500 \xd1\x80\xd1\x83\xd0\xb1. \xd0\xbc\xd0\xb8\xd0\xbd\xd0\xb8\xd0\xbc\xd1\x83\xd0\xbc. \xd0\x98 \xd0\xb7\xd0\xb4\xd0\xb5\xd1\x81\xd1\x8c \xd0\xb1\xd1\x83\xd0\xb4\xd0\xb5\xd1\x82 \xd1\x82\xd0\xbe\xd0\xb6\xd0\xb5 \xd1\x81\xd0\xb0\xd0\xbc\xd0\xbe\xd0\xb5, \xd0\xb2\xd1\x80\xd0\xbe\xd0\xb4\xd0\xb5 \xd0\xb1\xd1\x8b \xd0\xb8 \xd1\x81\xd1\x82. 26 \xd0\x9a\xd0\xbe\xd0\xbd\xd1\x81\xd1\x82\xd0\xb8\xd1\x82\xd1\x83\xd1\x86\xd0\xb8\xd0\xb8 \xd0\xbd\xd0\xb8\xd0\xba\xd1\x82\xd0\xbe \xd0\xbd\xd0\xb5 \xd0\xbe\xd1\x82\xd0\xbc\xd0\xb5\xd0\xbd\xd1\x8f\xd0\xbb, \xd0\xb0 \xd0\xb7\xd0\xb0 \xd0\xbd\xd0\xb5 \xd1\x83\xd0\xba\xd0\xb0\xd0\xb7\xd0\xb0\xd0\xbd\xd0\xb8\xd0\xb5 \xd1\x81\xd0\xb2\xd0\xb5\xd0\xb4\xd0\xb5\xd0\xbd\xd0\xb8\xd0\xb9 \xd0\xb2 \xd1\x80\xd0\xb0\xd0\xb7\xd0\xb4\xd0\xb5\xd0\xbb\xd0\xb5 \\"\xd0\xbd\xd0\xb0\xd1\x86\xd0\xb8\xd0\xbe\xd0\xbd\xd0\xb0\xd0\xbb\xd1\x8c\xd0\xbd\xd0\xbe\xd1\x81\xd1\x82\xd1\x8c\\" \xd0\xbd\xd0\xb0\xd1\x88\xd0\xb5 \xd1\x80\xd0\xbe\xd0\xb4\xd0\xbd\xd0\xbe\xd0\xb5 \xd0\xb3\xd0\xbe\xd1\x81\xd1\x83\xd0\xb4\xd0\xb0\xd1\x80\xd1\x81\xd1\x82\xd0\xb2\xd0\xbe \xd1\x83\xd1\x81\xd1\x82\xd0\xb0\xd0\xbd\xd0\xbe\xd0\xb2\xd0\xb8\xd1\x82 \xd0\xba\xd0\xb0\xd0\xba\xd0\xbe\xd0\xb9-\xd0\xbd\xd0\xb8\xd0\xb1\xd1\x83\xd0\xb4\xd1\x8c \xd1\x88\xd1\x82\xd1\x80\xd0\xb0\xd1\x84. \xd0\xa3\xd0\xb6\xd0\xb5 \xd0\xbd\xd0\xb5 \xd0\xb7\xd0\xbd\xd0\xb0\xd1\x8e\xd1\x82 \xd0\xbf\xd0\xbe \xd0\xba\xd0\xb0\xd0\xba\xd0\xb8\xd0\xbc \xd0\xba\xd1\x80\xd0\xb8\xd1\x82\xd0\xb5\xd1\x80\xd0\xb8\xd1\x8f\xd0\xbc \xd0\xbd\xd0\xb0\xd1\x80\xd0\xbe\xd0\xb4 \xd0\xba\xd0\xb0\xd0\xba \xd0\xb1\xd0\xb0\xd1\x80\xd0\xb0\xd0\xbd\xd0\xbe\xd0\xb2 \xd0\xbf\xd0\xbe\xd1\x81\xd1\x87\xd0\xb8\xd1\x82\xd0\xb0\xd1\x82\xd1\x8c. ","likes":{"count":0,"user_likes":0,"can_like":1}},{"cid":195310,"uid":225734427,"from_id":225734427,"date":1386603316,"text":"\xd0\xbf\xd1\x80\xd0\xb5\xd0\xb7\xd0\xb8\xd1\x80\xd0\xb0\xd1\x8e \xd0\xbb\xd1\x8e\xd0\xb4\xd0\xb5\xd0\xb9 \xd0\xba\xd0\xbe\xd1\x82\xd0\xbe\xd1\x80\xd1\x8b\xd0\xb5 \xd1\x81\xd1\x82\xd0\xb5\xd1\x81\xd0\xbd\xd1\x8f\xd1\x8e\xd1\x82\xd1\x81\xd1\x8f \xd1\x81\xd0\xb2\xd0\xbe\xd0\xb5\xd0\xb9 \xd0\xbd\xd0\xb0\xd1\x86\xd0\xb8\xd0\xbe\xd0\xbd\xd0\xb0\xd0\xbb\xd1\x8c\xd0\xbd\xd0\xbe\xd1\x81\xd1\x82\xd0\xb8","likes":{"count":7,"user_likes":0,"can_like":1}},{"cid":195309,"uid":1441686,"from_id":1441686,"date":1386603180,"text":"\xd0\x9d\xd0\xb0\xd1\x86\xd0\xb8\xd0\xbe\xd0\xbd\xd0\xb0\xd0\xbb\xd1\x8c\xd0\xbd\xd1\x8b\xd0\xb9 \xd0\xb4\xd0\xbe\xd0\xbf\xd1\x80\xd0\xbe\xd1\x81, \xd1\x80\xd0\xb5\xd0\xba\xd0\xbe\xd0\xbc\xd0\xb5\xd0\xbd\xd0\xb4\xd1\x83\xd1\x8e! http:\\/\\/www.echo.msk.ru\\/blog\\/minkin\\/1116562-echo\\/ http:\\/\\/echo.msk.ru\\/blog\\/minkin\\/1116562-echo\\/","likes":{"count":0,"user_likes":0,"can_like":1}},{"cid":195308,"uid":213252379,"from_id":213252379,"date":1386603171,"text":"\xd0\x9f\xd1\x80\xd0\xbe\xd0\xb5\xd0\xba\xd1\x82 \xd0\xbe\xd0\xb4\xd0\xbd\xd0\xbe\xd0\xb7\xd0\xbd\xd0\xb0\xd1\x87\xd0\xbd\xd0\xbe \xd0\xbd\xd0\xb5 \xd0\xbf\xd1\x80\xd0\xbe\xd0\xba\xd0\xb0\xd1\x82\xd0\xb8\xd1\x82 \xd1\x81\xd0\xbe\xd0\xb3\xd0\xbb\xd0\xb0\xd1\x81\xd0\xbe\xd0\xb2\xd0\xb0\xd0\xbd\xd0\xb8\xd0\xb5 \xd0\xb2 \xd0\x9c\xd0\xb8\xd0\xbd\xd1\x8e\xd1\x81\xd1\x82\xd0\xb5)).","likes":{"count":1,"user_likes":0,"can_like":1}},{"cid":195307,"uid":160959903,"from_id":160959903,"date":1386603167,"text":"\xd0\x98 \xd1\x87\xd1\x82\xd0\xbe \xd0\xbc\xd0\xb5\xd0\xbd\xd1\x8f\xd0\xb5\xd1\x82?\xd0\x9b\xd1\x8e\xd0\xb4\xd0\xb8 \xd1\x80\xd0\xb5\xd1\x88\xd0\xb8\xd0\xbb\xd0\xb8 \xd0\xb1\xd1\x8b\xd1\x82\xd1\x8c \xd0\xb2\xd0\xbc\xd0\xb5\xd1\x81\xd1\x82\xd0\xb5,\xd0\xb4\xd0\xb0\xd0\xb9 \xd0\x91\xd0\x9e\xd0\x93.","likes":{"count":0,"user_likes":0,"can_like":1}},{"cid":195304,"uid":126980853,"from_id":126980853,"date":1386603102,"text":"5-\xd0\xb3\xd0\xbe \xd0\xbf\xd1\x83\xd0\xbd\xd0\xba\xd1\x82\xd0\xb0 \xd0\xb2 \xd0\xa4\xd0\xbe\xd1\x80\xd0\xbc\xd0\xb5 \xe2\x84\x96 1 \xd0\xb8\xd0\xbc \xd0\xbc\xd0\xb0\xd0\xbb\xd0\xbe \xf0\x9f\x98\x8a \xd0\xa1\xd0\xba\xd0\xb0\xd0\xb6\xd1\x83 - \xd1\x81\xd0\xb8\xd0\xb1\xd0\xb8\xd1\x80\xd1\x8f\xd0\xba, \xd0\xb1\xd0\xbb\xd0\xb8\xd0\xbd, \xd0\xbf\xd1\x83\xd1\x81\xd1\x82\xd1\x8c \xd0\xb4\xd0\xbe\xd0\xba\xd0\xb0\xd0\xb6\xd1\x83\xd1\x82, \xd1\x87\xd1\x82\xd0\xbe \xd0\xbd\xd0\xb5\xd0\xbf\xd1\x80\xd0\xb0\xd0\xb2 \xf0\x9f\x98\x8a","likes":{"count":0,"user_likes":0,"can_like":1}},{"cid":195303,"uid":99696,"from_id":99696,"date":1386603042,"text":"\xd0\x95\xd0\xb2\xd1\x80\xd0\xb0\xd0\xb7\xd0\xb8\xd0\xb5\xd1\x86!","likes":{"count":2,"user_likes":0,"can_like":1}},{"cid":195302,"uid":2091173,"from_id":2091173,"date":1386602981,"text":"\xd0\xbd\xd1\x83 \xd0\xb2\xd0\xbe\xd0\xbe\xd0\xb1\xd1\x89\xd0\xb5-\xd1\x82\xd0\xbe \xd0\xbd\xd0\xb0\xd1\x86\xd0\xb8\xd0\xbe\xd0\xbd\xd0\xb0\xd0\xbb\xd1\x8c\xd0\xbd\xd0\xbe\xd1\x81\xd1\x82\xd1\x8c \xd0\xb2 \xd0\xb1\xd0\xbb\xd0\xb0\xd0\xbd\xd0\xba\xd0\xb0\xd1\x85 \xd0\xb8 \xd0\xb1\xd1\x8b\xd0\xbb\xd0\xb0, \xd1\x82\xd0\xbe\xd0\xbb\xd1\x8c\xd0\xba\xd0\xbe \xd0\xb7\xd0\xb0\xd0\xbf\xd0\xbe\xd0\xbb\xd0\xbd\xd1\x8f\xd0\xbb\xd0\xb8 \xd0\xbf\xd0\xbe \xd0\xb6\xd0\xb5\xd0\xbb\xd0\xb0\xd0\xbd\xd0\xb8\xd1\x8e","likes":{"count":1,"user_likes":0,"can_like":1}},{"cid":195301,"uid":6717923,"from_id":6717923,"date":1386602934,"text":"\xd1\x82\xd0\xb0\xd0\xba \xd0\xb2\xd1\x80\xd0\xbe\xd0\xb4\xd0\xb5\xd0\xb6 \xd0\xbd\xd0\xb5\xd1\x82 \xd0\xbd\xd0\xb0\xd1\x86\xd0\xb8\xd0\xbe\xd0\xbd\xd0\xb0\xd0\xbb\xd1\x8c\xd0\xbd\xd0\xbe\xd1\x81\xd1\x82\xd0\xb8 \xd0\xb4\xd0\xbb\xd1\x8f \xd1\x80\xd1\x83\xd1\x81\xd1\x81\xd0\xba\xd0\xb8\xd1\x85. \xd0\xb5\xd0\xb5 \xd0\xb7\xd0\xb0\xd0\xbc\xd0\xb5\xd0\xbd\xd0\xb8\xd0\xbb\xd0\xb8 \xd0\xbd\xd0\xb0 \\"\xd0\xb3\xd0\xbe\xd1\x80\xd0\xb4\xd0\xbe\xd0\xb5\\" \xd1\x80\xd0\xbe\xd1\x81\xd1\x81\xd0\xb8\xd1\x8f\xd0\xbd\xd0\xb8\xd0\xbd","likes":{"count":0,"user_likes":0,"can_like":1}},{"cid":195300,"uid":56807327,"from_id":56807327,"date":1386602876,"text":"http:\\/\\/vk.com\\/photo-23482909_315789481","likes":{"count":0,"user_likes":0,"can_like":1}},{"cid":195299,"uid":165400079,"from_id":165400079,"date":1386602872,"text":"[id167496147|\xd0\x90\xd0\xbd\xd0\xb4\xd1\x80\xd0\xb5\xd0\xb9], \xd0\xbd\xd0\xb5, \xd1\x82\xd0\xbe\xd0\xbb\xd1\x8c\xd0\xba\xd0\xbe \xd0\xb4\xd0\xbb\xd0\xb8\xd0\xbd\xd1\x83 \xd0\xb8 \xd1\x80\xd0\xb0\xd0\xb7\xd0\xbc\xd0\xb5\xd1\x80 \xd0\xb3\xd1\x80\xd1\x83\xd0\xb4\xd0\xb8","likes":{"count":1,"user_likes":0,"can_like":1},"reply_to_uid":167496147,"reply_to_cid":195296},{"cid":195298,"uid":76332491,"from_id":76332491,"date":1386602852,"text":"\xd0\x90 \xd1\x87\xd0\xb5\xd0\xb3\xd0\xbe \xd1\x81\xd1\x82\xd0\xb5\xd1\x81\xd0\xbd\xd1\x8f\xd1\x82\xd1\x8c\xd1\x81\xd1\x8f?","likes":{"count":1,"user_likes":0,"can_like":1}},{"cid":195297,"uid":115228782,"from_id":115228782,"date":1386602852,"text":"\xd1\x8d\xd0\xbb\xd1\x8c\xd1\x84\xd1\x8b, \xd1\x85\xd0\xbe\xd0\xb1\xd0\xb1\xd0\xb8\xd1\x82\xd1\x8b, \xd0\xb3\xd0\xbe\xd0\xb1\xd0\xbb\xd0\xb8\xd0\xbd\xd1\x8b \xd0\xb8 \xd1\x82.\xd0\xb4.","likes":{"count":2,"user_likes":0,"can_like":1}},{"cid":195296,"uid":167496147,"from_id":167496147,"date":1386602836,"text":"\xd0\xb0 \xd0\xb4\xd0\xbb\xd0\xb8\xd0\xbd\xd1\x83 \xd0\xb8 \xd0\xb3\xd0\xbb\xd1\x83\xd0\xb1\xd0\xb8\xd0\xbd\xd1\x83 \xd0\xb8\xd0\xbc \xd0\xbd\xd0\xb5 \xd0\xbd\xd0\xb0\xd0\xb4\xd0\xbe \xd1\x83\xd0\xba\xd0\xb0\xd0\xb7\xd1\x8b\xd0\xb2\xd0\xb0\xd1\x82\xd1\x8c???","likes":{"count":8,"user_likes":0,"can_like":1}},{"cid":195295,"uid":70236500,"from_id":70236500,"date":1386602820,"text":"\xd0\x90 \xd0\xb2\xd0\xbe\xd0\xbe\xd0\xb1\xd1\x89\xd0\xb5, \xd1\x81\xd1\x82\xd1\x80\xd0\xb0\xd0\xbd\xd0\xbd\xd0\xbe \xd1\x8d\xd1\x82\xd0\xbe. \xd0\x98 \xd0\xb7\xd0\xb0\xd1\x87\xd0\xb5\xd0\xbc \xd0\xbe\xd0\xbd\xd0\xbe, \xd1\x84\xd0\xb0\xd1\x88\xd0\xb8\xd0\xb7\xd0\xbc \xd0\xb6\xd0\xb5","likes":{"count":4,"user_likes":0,"can_like":1}},{"cid":195294,"uid":156031418,"from_id":156031418,"date":1386602812,"text":"\xd0\xb4\xd0\xb0\xd0\xb2\xd0\xbd\xd0\xbe \xd0\xbf\xd0\xbe\xd1\x80\xd0\xb0.","likes":{"count":4,"user_likes":0,"can_like":1}},{"cid":195293,"uid":70236500,"from_id":70236500,"date":1386602804,"text":"\\"\xd0\x9c\xd0\xbd\xd0\xbe\xd0\xb3\xd0\xbe\xd0\xbd\xd0\xb0\xd1\x86\xd0\xb8\xd0\xbe\xd0\xbd\xd0\xb0\xd0\xbb\\"","likes":{"count":4,"user_likes":0,"can_like":1}}]}'
        kwargs = {'sort': 'desc', 'count': 90, 'need_likes': 1, 'post_id': 195292, 'offset': 0, 'preview_length': 0, 'owner_id': -23482909}
        comments = self.api.get('wall.getComments', **kwargs)
        self.assertEqual(len(comments), 36)

if __name__ == '__main__':
    unittest.main()