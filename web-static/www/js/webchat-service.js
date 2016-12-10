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
  
  webchatService.postNewRoomMessage = function(roomId, message, clientMessageId) {
    var postNewRoomMessageEndpoint = WebChatApiEndpoint + 'room/' + encodeURIComponent(roomId) + '/message';
    
    var postMessageData = {
      'version': '1',
      'message': message
    };
    
    if (!angular.isUndefined(clientMessageId)) {
      postMessageData['client-message-id'] = clientMessageId;
    }
    
    return $q(function(resolve, reject) {
      $http({
        method: 'POST',
        url: postNewRoomMessageEndpoint,
        data: postMessageData
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
  var exponentialBackoffMaxSeconds = 30;
  
  var clientSessionWatchIdCancelerMap = {};
  var canceledClientSessionWatchIdMap = {};
  var roomClosedReceivedEndpointMap = {};
  
  var getRetryDelaySeconds = function() {
    var exponentialDelaySeconds = Math.pow(consecutiveRoomSessionMessagePollErrors, 2);
    
    return Math.min(exponentialDelaySeconds, exponentialBackoffMaxSeconds);
  }
  
  var startWatchingRoomSessionMessages = function(clientSessionWatchId, messagesEndpoint, messagesReceivedCallback) {
    // Ensure we haven't already received the signal to stop.
    if (canceledClientSessionWatchIdMap.hasOwnProperty(clientSessionWatchId)) {
      return;
    }
    
    roomSessionMessageWatchPollLiveCounter++;
    
    var recursiveThis = this;
    var recursiveArgs = arguments;
    var liveCounterDecremented = false;
    
    var canceler = $q.defer();
    clientSessionWatchIdCancelerMap[clientSessionWatchId].push(canceler);
    
    var removeCancelerReference = function() {
      var index = clientSessionWatchIdCancelerMap[clientSessionWatchId].indexOf(canceler);
      if (index > -1) {
        clientSessionWatchIdCancelerMap[clientSessionWatchId].splice(index, 1);
      }
    }
    
    $http({
      method: 'GET',
      url: messagesEndpoint,
      timeout: canceler.promise
    })
    .success(function(angResponseObject) {
      removeCancelerReference();
      if (!liveCounterDecremented) {
        roomSessionMessageWatchPollLiveCounter--;
        liveCounterDecremented = true;
      }
      
      
      var messagesArray = angResponseObject.messages;
      var receiptHandles = angResponseObject["receipt-handles"];
      consecutiveRoomSessionMessagePollErrors = 0;
      
      if (messagesArray.length > 0) {
        for (var i = 0; i < messagesArray.length; i++) {
          var eachMessage = messagesArray[i];
          if (eachMessage.type == "ROOM_CLOSED") {
            roomClosedReceivedEndpointMap[messagesEndpoint] = true;
          }
        }
        messagesReceivedCallback(messagesArray);
        webchatService.acknowledgeRoomSessionMessages(messagesEndpoint, receiptHandles);
      }
      
      startWatchingRoomSessionMessages.apply(recursiveThis, recursiveArgs);
    })
    .error(function(errorReason, errorCode) {
      
      removeCancelerReference();
      if (!liveCounterDecremented) {
        roomSessionMessageWatchPollLiveCounter--;
        liveCounterDecremented = true;
      }
      
      if (errorReason == null && errorCode == -1 && canceledClientSessionWatchIdMap.hasOwnProperty(clientSessionWatchId)) {
        // Cancelled. No further action necessary.
      }
      else if (errorCode == 400 && roomClosedReceivedEndpointMap.hasOwnProperty(messagesEndpoint)) {
        console.log("Room assumed to be closed.");
      }
      else {
        consecutiveRoomSessionMessagePollErrors++;
        
        var retryDelaySeconds = getRetryDelaySeconds();
        console.log(
          "Error polling for room session messages (" + consecutiveRoomSessionMessagePollErrors + "). " + 
          "Retrying in " + retryDelaySeconds + " second(s)."
        );
        
        setTimeout(function() {
          startWatchingRoomSessionMessages.apply(recursiveThis, recursiveArgs);
        }, retryDelaySeconds * 1000);
      }
    })
  }
  
  webchatService.watchForRoomSessionMessages = function(roomId, sessionId, messagesReceivedCallback, concurrentRequestCount = 3) {
    
    var sessionUrl = WebChatApiEndpoint + 'room/' + roomId + '/session/' + sessionId;
    
    var getSessionMessagesEndpoint = sessionUrl + '/message';
    
    var newClientSessionWatchId = Guid.raw();
    clientSessionWatchIdCancelerMap[newClientSessionWatchId] = [];
    
    for (var i=0; i < concurrentRequestCount; i++) {
      startWatchingRoomSessionMessages(newClientSessionWatchId, getSessionMessagesEndpoint, messagesReceivedCallback);
    }
    
    return newClientSessionWatchId;
  }
  
  webchatService.stopWatchingForRoomSessionMessages = function(clientSessionWatchId) {
    
    canceledClientSessionWatchIdMap[clientSessionWatchId] = true;
    
    var cancelerArray = clientSessionWatchIdCancelerMap[clientSessionWatchId];
    
    if (!angular.isUndefined(cancelerArray)) {
      for (var i = 0; i < cancelerArray.length; i++) {
        var eachCanceler = cancelerArray[i];
        eachCanceler.resolve();
      }
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