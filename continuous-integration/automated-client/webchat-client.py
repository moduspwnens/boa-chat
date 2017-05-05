#!/usr/bin/env python3
"""webchat-client.py

Simulates a basic webchat client. Designed to be used from potentially many 
simultaneous Docker clients to see large chat volume.
"""

import os
import json
import time
import uuid
from urllib.parse import urlparse
import threading
import random
import hashlib
import traceback
import requests
from requests_aws4auth import AWS4Auth

sample_chat_messages = open("sample-chat-messages.txt").read().split("\n")

simultaneous_session_poller_count = 3
main_loop_delay_min = 1
main_loop_delay_max = 10

class WebchatClient():
    
    new_credentials_needed = True
    
    def __init__(self):
        print("Initializing web chat client.")
        self.username = os.environ["LOGIN_USERNAME"]
        self.password = os.environ["LOGIN_PASSWORD"]
        self.rest_api_base = os.environ["REST_API_BASE"]
        self.chat_room_id = os.environ["CHAT_ROOM_ID"]
        
        if not self.rest_api_base.endswith("/"):
            self.rest_api_base += "/"
        
        print(" > REST API Base: {}".format(self.rest_api_base))
        print(" > Username: {}".format(self.username))
        print(" > Password: {}".format(self.password))
        print(" > Chat room ID: {}".format(self.chat_room_id))
    
    def load_v4_signing_params(self):
        
        print("Fetching AWS v4 signing parameters...")
        
        r = requests.get(
            url="{}api".format(self.rest_api_base)
        )
        try:
            r.raise_for_status()
        except requests.exceptions.HTTPError as e:
            print("Response text: {}".format(r.text))
            raise
        
        response_payload = r.json()
        
        self.aws_v4_region = response_payload["aws-v4-sig"]["region"]
        self.aws_v4_service = response_payload["aws-v4-sig"]["service"]
        
        print("Region: {} Service: {}".format(
            self.aws_v4_region,
            self.aws_v4_service
        ))
    
    def load_v4_signing_params_if_necessary(self):
        if hasattr(self, "aws_v4_region") and hasattr(self, "aws_v4_service"):
            return
        
        return self.load_v4_signing_params()
    
    def do_login(self):
        
        print("Attempting login...")
        
        r = requests.post(
            url="{}user/login".format(self.rest_api_base),
            headers={
                "Content-Type": "application/json; charset=utf-8",
            },
            data=json.dumps({
                "email-address": self.username,
                "password": self.password
            })
        )
        try:
            r.raise_for_status()
        except requests.exceptions.HTTPError as e:
            print("Response text: {}".format(r.text))
            raise
        
        response_payload = r.json()
        
        self._process_credentials_retrieved_payload(response_payload)
        
        print("Login succeeded.")
    
    def refresh_credentials(self):
        
        if not hasattr(self, "refresh_token"):
            raise NoRefreshTokenAvailableException("No refresh token stored. Cannot refresh credentials.")
        
        print("Attempting credential refresh...")
        
        headers_dict = {
            "Content-Type": "application/json; charset=utf-8"
        }
        
        if hasattr(self, "api_key"):
            headers_dict["x-api-key"] = self.api_key
        
        r = requests.post(
            url = "{}user/refresh".format(self.rest_api_base),
            headers = headers_dict,
            data = json.dumps({
                "refresh-token": self.refresh_token,
                "user-id": self.user_id
            })
        )
        try:
            r.raise_for_status()
        except requests.exceptions.HTTPError as e:
            print("Response text: {}".format(r.text))
            raise
        
        response_payload = r.json()
        
        self._process_credentials_retrieved_payload(response_payload)
        
        print("Credentials refreshed successfully.")
    
    def fetch_credentials_if_necessary(self):
        
        if self.new_credentials_needed:
            try:
                self.refresh_credentials()
            except NoRefreshTokenAvailableException as e:
                pass
            except Exception as e:
                print("Unable to refresh credentials: {}".format(e))
            
            self.do_login()
    
    def _process_credentials_retrieved_payload(self, response_payload):
        self.secret_access_key = response_payload["credentials"]["secret-access-key"]
        self.access_key_id = response_payload["credentials"]["access-key-id"]
        self.session_token = response_payload["credentials"]["session-token"]
        self.refresh_token = response_payload["credentials"]["refresh-token"]
        self.user_id = response_payload["user"]["user-id"]
        if "api-key" in response_payload["user"]:
            self.api_key = response_payload["user"]["api-key"]
        
        self.request_auth = AWS4Auth(
            self.access_key_id,
            self.secret_access_key,
            self.aws_v4_region,
            self.aws_v4_service,
            session_token = self.session_token
        )
        
        self.new_credentials_needed = False
    
    def create_room_session(self):
        
        if self.new_credentials_needed:
            raise Exception("New credentials are needed to make this request.")
        
        print("Creating room session...")
        
        headers_dict = {
            "Content-Type": "application/json; charset=utf-8"
        }
        
        if hasattr(self, "api_key"):
            headers_dict["x-api-key"] = self.api_key
        
        r = requests.post(
            url = "{}room/{}/session".format(self.rest_api_base, self.chat_room_id),
            headers = headers_dict,
            data = json.dumps({
                "refresh-token": self.refresh_token,
                "user-id": self.user_id
            }),
            auth = self.request_auth
        )
        try:
            r.raise_for_status()
        except requests.exceptions.HTTPError as e:
            print("Response text: {}".format(r.text))
            raise
        
        response_payload = r.json()
        
        self.chat_room_session_id = response_payload["id"]
        
        print("Room session created: {}".format(self.chat_room_session_id))
        
    def create_room_session_if_necessary(self):
        if hasattr(self, "chat_room_session_id"):
            return
        
        return self.create_room_session()
    
    def start_polling_for_new_messages(self):
        
        new_poller_list = []
        
        i = 0
        while i < simultaneous_session_poller_count:
            new_poller = RoomSessionMessagePoller(self)
            new_poller.start()
            new_poller_list.append(new_poller)
            i += 1
        
        self.chat_room_session_pollers = new_poller_list
    
    def start_polling_for_new_messages_if_necessary(self):
        if hasattr(self, "chat_room_session_pollers"):
            return
        
        self.start_polling_for_new_messages()
    
    def post_message(self, message_content):
        
        if self.new_credentials_needed:
            raise Exception("New credentials are needed to make this request.")
        
        print("Posting message ({})...".format(message_content))
        
        headers_dict = {
            "Content-Type": "application/json; charset=utf-8"
        }
        
        if hasattr(self, "api_key"):
            headers_dict["x-api-key"] = self.api_key
        
        r = requests.post(
            url = "{}room/{}/message".format(self.rest_api_base, self.chat_room_id),
            headers = headers_dict,
            data = json.dumps({
                "version": "1",
                "message": message_content,
                "client-message-id": str(uuid.uuid4())
            }),
            auth = self.request_auth
        )
        try:
            r.raise_for_status()
        except requests.exceptions.HTTPError as e:
            print("Response text: {}".format(r.text))
            raise
        
        response_payload = r.json()
        
        print("Message posted. ID: {}.".format(response_payload.get("message-id")))
    
    def do_main_loop(self):
        
        try:
            while True:
                
                error_did_occur = False
                
                try:
                    self.load_v4_signing_params_if_necessary()
            
                    self.fetch_credentials_if_necessary()
            
                    self.create_room_session_if_necessary()
            
                    self.start_polling_for_new_messages_if_necessary()
                    
                    delay_seconds = random.randint(main_loop_delay_min, main_loop_delay_max)
                    
                    time.sleep(delay_seconds)
                    
                    new_chat_message = random.choice(sample_chat_messages)
                    self.post_message(new_chat_message)
                    
                except requests.exceptions.HTTPError as e:
                    error_did_occur = True
                    
                    if str(e.response.status_code) == "400":
                        print("Received HTTP 400 response in main loop. Stopping.")
                        break
                    
                except Exception as e:
                    error_did_occur = True
                    print("Error in main loop: {}".format(e))
                    print(traceback.format_exc())
                
                if error_did_occur:
                    time.sleep(30 + random.randint(0,9))
        
        except KeyboardInterrupt:
            pass
        
        if hasattr(self, "chat_room_session_pollers"):
            for each_poller in self.chat_room_session_pollers:
                each_poller.stop()

class RoomSessionMessagePoller(object):
    
    stopped = False
    receipt_handles = {}
    instance_id = str(uuid.uuid4())
    
    def __init__(self, new_client):
        self.client = new_client
    
    def stop(self):
        self.stopped = True
    
    def start(self):
        threading.Thread(target=self._run).start()
    
    def _run(self):
        while True:
            
            if self.stopped:
                break
            
            error_did_occur = False
            
            try:
                self.fetch_new_messages()
                self.acknowledge_received_messages()
                time.sleep(1)
            
            except requests.exceptions.HTTPError as e:
                error_did_occur = True
                if str(e.response.status_code) == "403":
                    print("Setting flag that credentials need to be reset.")
                    self.client.new_credentials_needed = True
                elif str(e.response.status_code) == "400":
                    print("Received HTTP 400 response polling for messages. Stopping.")
                    break
                
            except Exception as e:
                error_did_occur = True
                print("Error polling for new messages: {}".format(e))
                print(traceback.format_exc())
            
            if error_did_occur:
                time.sleep(30 + random.randint(0,9))
    
    def fetch_new_messages(self):
        
        if self.client.new_credentials_needed:
            raise Exception("New credentials are needed to make this request.")
        
        if not hasattr(self.client, "chat_room_session_id"):
            raise Exception("No chat room session available.")
        
        #print("Checking for messages in room session ({})...".format(self.client.chat_room_session_id))
        
        headers_dict = {
            "Content-Type": "application/json; charset=utf-8"
        }
        
        if hasattr(self.client, "api_key"):
            headers_dict["x-api-key"] = self.client.api_key
        
        r = requests.get(
            url = "{}room/{}/session/{}/message".format(self.client.rest_api_base, self.client.chat_room_id, self.client.chat_room_session_id),
            headers = headers_dict,
            auth = self.client.request_auth
        )
        try:
            r.raise_for_status()
        except requests.exceptions.HTTPError as e:
            print("Response text: {}".format(r.text))
            raise
        
        try:
            response_payload = r.json()
        except:
            print("Original text: {}".format(r.text))
            raise
        
        if len(response_payload["messages"]) == 0:
            return
        
        for each_handle in response_payload["receipt-handles"]:
            self.receipt_handles[each_handle] = True
        
        for each_message in response_payload["messages"]:
            print("Chat message from {}: {}".format(
                each_message["author-name"],
                each_message["message"]
            ))
    
    def acknowledge_received_messages(self):
        if len(self.receipt_handles) == 0:
            return
        
        if self.client.new_credentials_needed:
            raise Exception("New credentials are needed to make this request.")
        
        if not hasattr(self.client, "chat_room_session_id"):
            raise Exception("No chat room session available.")
        
        receipt_handles_to_acknowledge = list(self.receipt_handles.keys())
        
        #print("Acknowledging receipt of {} message(s)...".format(len(receipt_handles_to_acknowledge)))
        
        headers_dict = {
            "Content-Type": "application/json; charset=utf-8"
        }
        
        if hasattr(self.client, "api_key"):
            headers_dict["x-api-key"] = self.client.api_key
        
        r = requests.put(
            url = "{}room/{}/session/{}/message".format(self.client.rest_api_base, self.client.chat_room_id, self.client.chat_room_session_id),
            headers = headers_dict,
            data = json.dumps({
                "receipt-handles": receipt_handles_to_acknowledge
            }),
            auth = self.client.request_auth
        )
        try:
            r.raise_for_status()
        except requests.exceptions.HTTPError as e:
            print("Response text: {}".format(r.text))
            raise
        
        for each_handle in receipt_handles_to_acknowledge:
            try:
                del self.receipt_handles[each_handle]
            except KeyError as e:
                pass

class NoRefreshTokenAvailableException(Exception):
    pass

if __name__ == "__main__":
    new_client = WebchatClient()
    new_client.do_main_loop()