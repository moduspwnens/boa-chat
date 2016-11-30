'use strict';

app.controller('roomController', function($scope, $http, $stateParams, webchatService) {
  
  $scope.roomChatEvents = [];
  $scope.messageInputDisabled = true;
  $scope.messageInputTextPlaceholder = "Joining room...";
  
  $scope.identityIdAuthorNameMap = {};
  
  var roomId = $stateParams.roomId;
  var userId = "Me";
  
  var unsentMessageIdIndex = 0;
  var sentUnsentMessageIdMap = {};
  
  var roomChatEventComparator = function(a, b) {
    // Try to sort by timestamp first.
    var timestampComparison = (a.timestamp - b.timestamp);
    if (timestampComparison != 0) {
      return timestampComparison;
    }
    
    // If the timestamps match, sort by message text.
    // It's arbitrary, but will result in consistent ordering among different 
    // clients.
    
    if (a.message < b.message) {
      return -1;
    }
    else if (a.message > b.message) {
      return 1;
    }
    return 0;
  }
  
  var newMessagesReceived = function(messageArray) {
    for (var i=0; i < messageArray.length; i++) {
      var eachMessage = messageArray[i];
      
      if (sentUnsentMessageIdMap.hasOwnProperty(eachMessage["message-id"])) {
        var unsentMessage = sentUnsentMessageIdMap[eachMessage["message-id"]];
        unpostUnsentMessage(unsentMessage);
        delete sentUnsentMessageIdMap[eachMessage["message-id"]];
      }
      
      $scope.identityIdAuthorNameMap[eachMessage["identity-id"]] = eachMessage["author-name"];
      
      $scope.roomChatEvents.push(eachMessage);
      $scope.roomChatEvents.sort(roomChatEventComparator);
      
    }
  }
  
  var unpostUnsentMessage = function(unsentMessage) {
    var unsentMessageIndex = $scope.roomChatEvents.indexOf(unsentMessage);
    if (unsentMessageIndex > -1) {
      $scope.roomChatEvents.splice(unsentMessageIndex, 1);
    }
  }
  
  var focusSendMessageBox = function() {
    window.setTimeout(function() {
      document.getElementById("message-input").focus();
    }, 0);
  }
  
  webchatService.createNewRoomSession(roomId)
    .then(function(angResponseObject) {
      var sessionUrl = angResponseObject.session;
      
      webchatService.watchForRoomSessionMessages(sessionUrl, newMessagesReceived);
      $scope.messageInputTextPlaceholder = "Send a message";
      $scope.messageInputDisabled = false;
      
      focusSendMessageBox();
      
    })
    .catch(function() {
      alert("An error occurred in trying to enter the room.");
    });
  
  
  var postUnsentMessage = function(messageText) {
    var unsentMessageObject = {
      "message-id": unsentMessageIdIndex,
      "timestamp": Math.floor(Date.now() / 1000),
      "identity-id": userId,
      "author-name": userId,
      "message": messageText,
      "unsent": true
    };
    
    newMessagesReceived([unsentMessageObject]);
    
    unsentMessageIdIndex++;
    
    return unsentMessageObject;
  }
  
  $scope.messageSendFormSubmitted = function() {
    
    var messageText = $scope.messageInputText;
    
    var unsentMessage = postUnsentMessage(messageText);
    $scope.messageInputText = "";
    focusSendMessageBox();
    
    var postRoomId = roomId;
    
    webchatService.postNewRoomMessage(postRoomId, messageText)
      .then(function(messageId) {
        sentUnsentMessageIdMap[messageId] = unsentMessage;
      })
      .catch(function() {
        unsentMessage["send-failure"] = true;
      })
    
  }
  
});