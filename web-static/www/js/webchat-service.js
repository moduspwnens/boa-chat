'use strict';

angular.module('webchatService', ['webchatApiEndpoint'])
.factory('webchatService', function($http, $q, $cookieStore, WebChatApiEndpoint) {
  
  var webchatService = {};
  
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
        resolve(angResponseObject["registration-id"]);
      })
      .error(function(angResponseObject, errorCode) {
        console.log(arguments);
        reject("Other");
      })
    });
  }
  
  webchatService.confirmUserEmailAddress = function(registrationId, token) {
    var registerEndpoint = WebChatApiEndpoint + 'user/register/verify';
    
    return $q(function(resolve, reject) {
      $http({
        method: 'GET',
        url: registerEndpoint,
        params: {
          "registration-id": registrationId,
          "token": token
        }
      })
      .success(function(angResponseObject) {
        resolve(true);
      })
      .error(function(angResponseObject, errorCode) {
        if (errorCode == 400 && angResponseObject.hasOwnProperty("message")) {
          reject(angResponseObject.message);
        }
        else {
          reject("Other");
        }
      })
    });
  }
  
  webchatService.getCurrentUser = function() {
    var userLoginObject = $cookieStore.get("login");
    
    if (!angular.isUndefined(userLoginObject)) {
      return userLoginObject.user;
    }
    
    return undefined;
  }
  
  webchatService.getCurrentUserCredentials = function() {
    var userLoginObject = $cookieStore.get("login");
    if ((!angular.isUndefined(userLoginObject)) && !angular.isUndefined(userLoginObject.credentials)) {
      // Clear credentials due to assumed expiry?
    }
    else {
      return undefined;
    }
    
    return userLoginObject.credentials;
  }
  
  webchatService.isUserLoggedIn = function() {
    var returnValue = (webchatService.getCurrentUser() !== undefined);
    return returnValue;
  }
  
  var processNewLoginResponse = function(responseObject) {
    var expirationSeconds = responseObject.credentials.expiration;
    
    var expirationDateTime = new Date();
    expirationDateTime.setSeconds(expirationDateTime.getSeconds() + expirationSeconds);
    
    var cookieStoreObject = responseObject;
    cookieStoreObject.credentials.expiration = expirationDateTime;
    
    $cookieStore.put("login", cookieStoreObject);
    
    resetCredentialRefreshTimer();
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
        
        processNewLoginResponse(angResponseObject);
        
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
  
  var refreshCurrentUserCredentials = function() {
    console.log("Attempting to refresh credentials.");
    
    var userObject = webchatService.getCurrentUser();
    var credentials = webchatService.getCurrentUserCredentials();
    
    var refreshCredentialsEndpoint = WebChatApiEndpoint + 'user/refresh';
    
    $http({
      method: 'POST',
      url: refreshCredentialsEndpoint,
      data: {
        "user-id": userObject["user-id"],
        "refresh-token": credentials["refresh-token"]
      }
    })
    .success(function(angResponseObject) {
      
      processNewLoginResponse(angResponseObject);
      
      console.log("Credentials refreshed successfully.");
    })
    .error(function(angResponseObject, errorCode) {
      console.log("An error occurred in refreshing credentials. Logging out.");
      console.log(arguments);
      
      webchatService.logOut();
    })
    
  }
  
  webchatService.logOut = function() {
    return $q(function(resolve, reject) {
      $cookieStore.put("login", undefined);
      
      resetCredentialRefreshTimer();
      
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
        resolve(angResponseObject["id"]);
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
        resolve(angResponseObject["id"]);
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
  
  webchatService.watchForRoomSessionMessages = function(roomId, sessionId, messagesReceivedCallback, concurrentRequestCount = 3) {
    
    var sessionUrl = WebChatApiEndpoint + 'room/' + roomId + '/session/' + sessionId;
    
    var getSessionMessagesEndpoint = sessionUrl + '/message';
    
    for (var i=0; i < concurrentRequestCount; i++) {
      startWatchingRoomSessionMessages(getSessionMessagesEndpoint, messagesReceivedCallback);
    }
  }
  
  var credentialRefreshTimer = undefined;
  
  var resetCredentialRefreshTimer = function() {
    
    // Clear the existing timer (if it exists).
    if (!angular.isUndefined(credentialRefreshTimer)) {
      console.log("Clearing credential refresh timer.");
      clearTimeout(credentialRefreshTimer);
      credentialRefreshTimer = undefined;
    }
    
    var credentials = webchatService.getCurrentUserCredentials();
    if (angular.isUndefined(credentials)) {
      // No credentials set. No need to set refresh timer.
      return;
    }
    
    var expirationDateTime = new Date(credentials.expiration);
    var secondsUntilExpiration = (expirationDateTime.getTime() - (new Date()).getTime()) / 1000;
    
    var secondsUntilRefresh = (secondsUntilExpiration * 0.9);
    
    console.log("Setting timer for refreshing credentials in " + secondsUntilRefresh + " seconds.");
    
    credentialRefreshTimer = setTimeout(refreshCurrentUserCredentials, secondsUntilRefresh * 1000);
    
  }
  
  resetCredentialRefreshTimer();
  
  return webchatService;
});