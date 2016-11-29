'use strict';

angular.module('webchatService', ['webchatApiEndpoint'])
.factory('webchatService', function($http, $q, $cookieStore, WebChatApiEndpoint) {
  
  var webchatService = {};
  
  webchatService.getApiSettings = function() {
    var apiSettingsEndpoint = WebChatApiEndpoint + 'api.json';
    
    return $q(function(resolve, reject) {
      $http({
        url: apiSettingsEndpoint
      })
      .success(function(angResponseObject) {
        resolve(angResponseObject["user-id"]);
      })
      .error(function(angResponseObject, errorCode) {
        console.log(arguments);
        reject("Other");
      })
    });
  }
  
  webchatService.registerUser = function(emailAddress, password) {
    var registerEndpoint = WebChatApiEndpoint + 'user/register';
    
    return $q(function(resolve, reject) {
      $http({
        method: 'POST',
        url: registerEndpoint,
        headers: {
          "content-type": "application/json"
        },
        data: {
          "email-address": emailAddress,
          "password": password
        }
      })
      .success(function(angResponseObject) {
        resolve(angResponseObject["user-id"]);
      })
      .error(function(angResponseObject, errorCode) {
        console.log(arguments);
        reject("Other");
      })
    });
  }
  
  webchatService.getCurrentUserCredentials = function() {
    return $cookieStore.get("credentials");
  }
  
  webchatService.isUserLoggedIn = function() {
    var returnValue = (webchatService.getCurrentUserCredentials() !== undefined);
    return returnValue;
  }
  
  webchatService.logIn = function(emailAddress, password) {
    var loginEndpoint = WebChatApiEndpoint + 'user/login';
    return $q(function(resolve, reject) {
      $http({
        method: 'POST',
        url: loginEndpoint,
        data: {
          "email-address": emailAddress,
          "password": password
        }
      })
      .success(function(angResponseObject) {
        
        var expirationSeconds = angResponseObject.expiration;
        
        // Assume it expires a little early to enforce early credential refresh.
        expirationSeconds *= 0.9;
        
        var expirationDateTime = new Date();
        expirationDateTime.setSeconds(expirationDateTime.getSeconds() + expirationSeconds);
        
        var cookieStoreObject = angResponseObject;
        cookieStoreObject.expiration = expirationDateTime;
        cookieStoreObject.emailAddress = emailAddress;
        
        $cookieStore.put("credentials", cookieStoreObject);
        
        resolve(angResponseObject);
      })
      .error(function(angResponseObject, errorCode) {
        console.log(arguments);
        if (errorCode == 404) {
          reject("UserNotFound");
        }
        else if (errorCode == 403 && angResponseObject.message == "Password entered is not correct.") {
          reject("PasswordIncorrect");
        }
        else {
          reject("Other");
        }
      })
    });
  }
  
  webchatService.logOut = function() {
    return $q(function(resolve, reject) {
      $cookieStore.put("credentials", undefined);
      
      resolve();
    });
  }
  
  var createRoomEndpoint = WebChatApiEndpoint + "room";
  
  webchatService.createNewRoom = function() {
    return $q(function(resolve, reject) {
      
      $http({
        method: 'POST',
        url: createRoomEndpoint,
        data: ""
      })
      .success(function(angResponseObject) {
        resolve(angResponseObject);
      })
      .error(function() {
        reject(arguments);
      })
    });
  }
  
  webchatService.createNewRoomSession = function(roomId) {
    var createRoomSessionEndpoint = WebChatApiEndpoint + 'room/' + encodeURIComponent(roomId) + '/session';
    
    return $q(function(resolve, reject) {
      
      $http({
        method: 'POST',
        url: createRoomSessionEndpoint,
        data: ""
      })
      .success(function(angResponseObject) {
        resolve(angResponseObject);
      })
      .error(function() {
        reject(arguments);
      })
    });
  }
  
  webchatService.postNewRoomMessage = function(roomId, message) {
    var postNewRoomMessageEndpoint = WebChatApiEndpoint + 'room/' + encodeURIComponent(roomId) + '/message';
    
    return $q(function(resolve, reject) {
      $http({
        method: 'POST',
        url: postNewRoomMessageEndpoint,
        data: {
          'version': '1',
          'message': message
        }
      })
      .success(function(angResponseObject) {
        resolve(angResponseObject["message-id"]);
      })
      .error(function() {
        reject(arguments);
      })
    });
  }
  
  webchatService.acknowledgeRoomSessionMessages = function(messagesEndpoint, receiptHandleArray) {
    return $q(function(resolve, reject) {
      $http({
        method: 'PUT',
        url: messagesEndpoint,
        data: {
          'receipt-handles': receiptHandleArray
        }
      })
      .success(function() {
        resolve();
      })
      .error(function() {
        reject(arguments);
      })
    });
  }
  
  var roomSessionMessageWatchActive = false;
  var roomSessionMessageWatchPollLiveCounter = 0;
  var consecutiveRoomSessionMessagePollErrors = 0;
  
  var startWatchingRoomSessionMessages = function(messagesEndpoint, messagesReceivedCallback) {
    roomSessionMessageWatchPollLiveCounter++;
    
    var recursiveThis = this;
    var recursiveArgs = arguments;
    var liveCounterDecremented = false;
    
    $http({
      method: 'GET',
      url: messagesEndpoint
    })
    .success(function(angResponseObject) {
      if (!liveCounterDecremented) {
        roomSessionMessageWatchPollLiveCounter--;
        liveCounterDecremented = true;
      }
      
      
      var messagesArray = angResponseObject.messages;
      var receiptHandles = angResponseObject["receipt-handles"];
      consecutiveRoomSessionMessagePollErrors = 0;
      
      if (messagesArray.length > 0) {
        messagesReceivedCallback(messagesArray);
        webchatService.acknowledgeRoomSessionMessages(messagesEndpoint, receiptHandles);
      }
      
      startWatchingRoomSessionMessages.apply(recursiveThis, recursiveArgs);
    })
    .error(function() {
      if (!liveCounterDecremented) {
        roomSessionMessageWatchPollLiveCounter--;
        liveCounterDecremented = true;
      }
      
      consecutiveRoomSessionMessagePollErrors++;
      console.log("Error polling for room session messages (" + consecutiveRoomSessionMessagePollErrors + ").");
      startWatchingRoomSessionMessages.apply(recursiveThis, recursiveArgs);
    })
  }
  
  webchatService.watchForRoomSessionMessages = function(sessionUrl, messagesReceivedCallback, concurrentRequestCount = 3) {
    var getSessionMessagesEndpoint = sessionUrl + '/message';
    
    for (var i=0; i < concurrentRequestCount; i++) {
      startWatchingRoomSessionMessages(getSessionMessagesEndpoint, messagesReceivedCallback);
    }
  }
  
  return webchatService;
});