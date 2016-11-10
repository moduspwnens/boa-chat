'use strict';

angular.module('webchatService', [])
.factory('webchatService', function($http, $q) {
  
  var webchatService = {};
  
  /*
    isCorsConfigured
  
    Used to verify that the CORS-allowed Origin allows the web site from 
    which the browser is currently accessing it.
  */
  var isCorsConfigured = function() {
    var corsOriginsArray = CorsOriginList.split(",");
    
    var actualOrigin = location.protocol + "//" + location.hostname;
    
    for (var i = 0; i < corsOriginsArray.length; i++) {
      var eachOrigin = corsOriginsArray[i];
      if (eachOrigin == "*") {
        return true;
      }
      else if (eachOrigin == actualOrigin) {
        return true;
      }
    }
    return false;
  }
  
  var createRoomEndpoint = WebChatApiEndpoint + "room"
  
  webchatService.createNewRoom = function() {
    return $q(function(resolve, reject) {
      if (!isCorsConfigured()) {
        reject('cors');
      }
      
      $http({
        method: 'POST',
        url: createRoomEndpoint
      })
      .success(function(angResponseObject) {
        resolve(angResponseObject);
      })
      .error(function() {
        reject(arguments);
      })
    });
  }
  
  webchatService.createNewRoomSession = function(roomId, userId) {
    var createRoomSessionEndpoint = WebChatApiEndpoint + 'room/' + encodeURIComponent(roomId) + '/session';
    
    return $q(function(resolve, reject) {
      if (!isCorsConfigured()) {
        reject('cors');
      }
      
      $http({
        method: 'POST',
        url: createRoomSessionEndpoint,
        data: {
          'user-id': userId
        }
      })
      .success(function(angResponseObject) {
        resolve(angResponseObject);
      })
      .error(function() {
        reject(arguments);
      })
    });
  }
  
  webchatService.postNewRoomMessage = function(roomId, userId, message) {
    var postNewRoomMessageEndpoint = WebChatApiEndpoint + 'room/' + encodeURIComponent(roomId) + '/message';
    
    return $q(function(resolve, reject) {
      $http({
        method: 'POST',
        url: postNewRoomMessageEndpoint,
        data: {
          'version': '1',
          'message': message,
          'user-id': userId
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