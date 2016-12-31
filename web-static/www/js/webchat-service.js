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
      .then(function(response) {
        resolve(response["data"]["registration-id"]);
      }, function(response) {
        
        if (response.status == 400) {
          reject(response["data"]["message"])
        }
        else {
          reject("Other");
        }
        
      })
    });
  }
  
  webchatService.confirmRegistrationEmailAddress = function(registrationId, token) {
    var registerEndpoint = WebChatApiEndpoint + 'user/register/verify';
    
    var requestParams = {
      "registration-id": registrationId,
      "token": token
    };
    
    return $q(function(resolve, reject) {
      $http({
        method: 'GET',
        url: registerEndpoint,
        params: requestParams
      })
      .then(function(response) {
        resolve(response["data"]["email-address"]);
      }, function(response) {
        
        if (response.status == 400) {
          reject(response["data"]["message"]);
        }
        else {
          reject("Other");
        }
      })
    });
  }
  
  webchatService.confirmChangedEmailAddress = function(token) {
    var registerEndpoint = WebChatApiEndpoint + 'user/email/verify';
    
    return $q(function(resolve, reject) {
      $http({
        method: 'GET',
        url: registerEndpoint,
        params: {
          "token": token
        },
        includeApiKey: true,
        sign: true
      })
      .then(function(response) {
        resolve(response["data"]["email-address"]);
      }, function(response) {
        if (response.status == 400) {
          reject(response["data"]["message"]);
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
      .then(function(response) {
        
        processNewLoginResponse(response["data"]);
        
        resolve(response["data"]);
      }, function(response) {
        if (response.status == 400) {
          reject(response["data"]["message"]);
        }
        else {
          reject("Other");
        }
      })
    });
  }
  
  webchatService.requestPasswordResetCode = function(emailAddress) {
    var requestEndpoint = WebChatApiEndpoint + 'user/forgot';
    return $q(function(resolve, reject) {
      $http({
        method: 'POST',
        url: requestEndpoint,
        data: {
          "email-address": emailAddress
        }
      })
      .then(function(response) {
        resolve(response["data"]);
      }, function(response) {
        
        if (response.status == 400) {
          reject(response["data"]["message"]);
        }
        else {
          reject("Other");
        }
      })
    });
  }
  
  webchatService.changePasswordWithResetCode = function(emailAddress, password, resetCode) {
    var requestEndpoint = WebChatApiEndpoint + 'user/forgot/password';
    return $q(function(resolve, reject) {
      $http({
        method: 'POST',
        url: requestEndpoint,
        data: {
          "email-address": emailAddress,
          "password": password,
          "token": resetCode
        }
      })
      .then(function(response) {
        resolve(response["data"]);
      }, function(response) {
        
        if (response.status == 400) {
          reject(response["data"]["message"]);
        }
        else {
          reject("Other");
        }
      })
    });
  }
  
  webchatService.changePasswordWithExistingPassword = function(existingPassword, newPassword) {
    var requestEndpoint = WebChatApiEndpoint + 'user/password';
    return $q(function(resolve, reject) {
      $http({
        method: 'POST',
        url: requestEndpoint,
        data: {
          "old-password": existingPassword,
          "password": newPassword
        },
        includeApiKey: true,
        sign: true
      })
      .then(function(response) {
        resolve(response["data"]);
      }, function(response) {
        
        if (response.status == 400) {
          reject(response["data"]["message"]);
        }
        else {
          reject("Other");
        }
      })
    });
  }
  
  webchatService.requestEmailAddressChange = function(newEmailAddress) {
    var requestEndpoint = WebChatApiEndpoint + 'user';
    return $q(function(resolve, reject) {
      $http({
        method: 'PATCH',
        url: requestEndpoint,
        data: {
          "email-address": newEmailAddress
        },
        includeApiKey: true,
        sign: true
      })
      .then(function(response) {
        resolve(response["data"]["registration-id"]);
      }, function(response) {
        
        if (response.status == 400) {
          reject(response["data"]["message"]);
        }
        else {
          reject("Other");
        }
      })
    });
  }
  
  webchatService.resetApiKey = function() {
    var requestEndpoint = WebChatApiEndpoint + 'user/api-key';
    return $q(function(resolve, reject) {
      $http({
        method: 'PUT',
        url: requestEndpoint,
        data: "",
        includeApiKey: true,
        sign: true
      })
      .then(function(response) {
        var newApiKey = response["data"]["api-key"];
        
        var cookieStoreObject = $cookieStore.get("login");
        cookieStoreObject["user"]["api-key"] = newApiKey;
        $cookieStore.put("login", cookieStoreObject);
        
        resolve(newApiKey);
      }, function(response) {
        if (response.status == 400) {
          reject(response["data"]["message"]);
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
      },
      includeApiKey: true
    })
    .then(function(response) {
      
      processNewLoginResponse(response["data"]);
      
      console.log("Credentials refreshed successfully.");
    }, function(response) {
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
  
  webchatService.createNewRoom = function() {
    var requestEndpoint = WebChatApiEndpoint + "room";
    
    return $q(function(resolve, reject) {
      
      $http({
        method: 'POST',
        url: requestEndpoint,
        data: "",
        sign: true,
        includeApiKey: true
      })
      .then(function(response) {
        resolve(response["data"]["id"]);
      }, function(response) {
        if (response.status == 400) {
          reject(response["data"]["message"]);
        }
        else {
          reject("Other");
        }
      })
    });
  }
  
  webchatService.createNewRoomSession = function(roomId) {
    var createRoomSessionEndpoint = WebChatApiEndpoint + 'room/' + encodeURIComponent(roomId) + '/session';
    
    return $q(function(resolve, reject) {
      
      $http({
        method: 'POST',
        url: createRoomSessionEndpoint,
        data: "",
        sign: true,
        includeApiKey: true
      })
      .then(function(response) {
        resolve(response["data"]["id"]);
      }, function(response) {
        if (response.status == 400) {
          reject(response["data"]["message"]);
        }
        else {
          reject("Other");
        }
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
        data: postMessageData,
        sign: true,
        includeApiKey: true
      })
      .then(function(response) {
        resolve(response["data"]["message-id"]);
      }, function(response) {
        if (response.status == 400) {
          reject(response["data"]["message"]);
        }
        else {
          reject("Other");
        }
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
        },
        sign: true,
        includeApiKey: true
      })
      .then(function() {
        resolve();
      }, function(response) {
        if (response.status == 400) {
          reject(response["data"]["message"]);
        }
        else {
          reject("Other");
        }
      })
    });
  }
  
  webchatService.getRoomMessageHistory = function(roomId, nextToken) {
    var requestEndpoint = WebChatApiEndpoint + 'room/' + encodeURIComponent(roomId) + '/message';
    
    var params = {
      direction: "reverse"
    };
    
    if (!angular.isUndefined(nextToken)) {
      params["next-token"] = nextToken;
    }
    
    return $q(function(resolve, reject) {
      $http({
        method: 'GET',
        url: requestEndpoint,
        params: params,
        sign: true,
        includeApiKey: true
      })
      .then(function(response) {
        resolve(response["data"]);
      }, function(response) {
        if (response.status == 400) {
          reject(response["data"]["message"]);
        }
        else {
          reject("Other");
        }
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
      timeout: canceler.promise,
      sign: true,
      includeApiKey: true
    })
    .then(function(response) {
      removeCancelerReference();
      if (!liveCounterDecremented) {
        roomSessionMessageWatchPollLiveCounter--;
        liveCounterDecremented = true;
      }
      
      
      var messagesArray = response["data"]["messages"];
      var receiptHandles = response["data"]["receipt-handles"];
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
    }, function(response) {
      
      removeCancelerReference();
      if (!liveCounterDecremented) {
        roomSessionMessageWatchPollLiveCounter--;
        liveCounterDecremented = true;
      }
      
      if (response.status == -1 && canceledClientSessionWatchIdMap.hasOwnProperty(clientSessionWatchId)) {
        // Cancelled. No further action necessary.
      }
      else if (response.status == 400 && roomClosedReceivedEndpointMap.hasOwnProperty(messagesEndpoint)) {
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