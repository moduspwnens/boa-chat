'use strict';

app.controller('roomController', function($scope, $http, $stateParams, $cookieStore, $uibModal, webchatService) {
  
  $scope.roomChatEvents = [];
  $scope.messageInputDisabled = true;
  $scope.messageInputTextPlaceholder = "Joining room...";
  
  $scope.identityIdAuthorNameMap = {};
  
  var roomId = $stateParams.roomId;
  var userId = "Me";
  
  var unsentMessageMap = {};
  var confirmedSentMessageIdMap = {};
  
  var recentRoomMessagesFetched = false;
  var clientRoomSessionWatchId = undefined;
  
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
  
  var newMessagesReceived = function(messageArray, unsent = false) {
    for (var i=0; i < messageArray.length; i++) {
      var eachMessage = messageArray[i];
      
      if (!unsent) {
        // Make sure we haven't already shown this message on the screen in 
        // anticipation of its sending being confirmed.
        
        var eachClientMessageId = eachMessage["client-message-id"];
        
        if (!angular.isUndefined(eachClientMessageId)) {
          // This message has already been shown on the screen.
          
          if (unsentMessageMap.hasOwnProperty(eachClientMessageId)) {
            // Receiving it now confirms its sending was successful.
            unsentMessageConfirmed(eachClientMessageId, eachMessage["message-id"]);
            continue;
          }
          
          if (confirmedSentMessageIdMap.hasOwnProperty(eachClientMessageId)) {
            // We already know this message was confirmed.
            continue;
          }
        }
      }
      
      $scope.identityIdAuthorNameMap[eachMessage["identity-id"]] = eachMessage["author-name"];
      
      $scope.roomChatEvents.push(eachMessage);
      $scope.roomChatEvents.sort(roomChatEventComparator);
      
    }
  }
  
  var focusSendMessageBox = function() {
    window.setTimeout(function() {
      document.getElementById("message-input").focus();
    }, 0);
  }
  
  var stopSessionWatchingSession = function(clientSessionId) {
    webchatService.stopWatchingForRoomSessionMessages(clientSessionId);
  }
  
  var fetchRecentRoomMessages = function() {
    webchatService.getRoomMessageHistory(roomId)
      .then(function(response) {
        var messageArray = response.messages;
        
        newMessagesReceived(messageArray);
        recentRoomMessagesFetched = true;
        
        evaluateIfReadyToPost();
        
        if (response.truncated) {
          console.log("Room has prior messages, too.");
        }
      })
      .catch(function(errorReason) {
        console.log("Error occurred fetching recent room messages.");
        console.log(errorReason);
      })
  }
  
  var createNewRoomSession = function() {
    webchatService.createNewRoomSession(roomId)
      .then(function(sessionId) {
      
        if (!angular.isUndefined(clientRoomSessionWatchId)) {
          stopSessionWatchingSession(clientRoomSessionWatchId);
          clientRoomSessionWatchId = undefined;
        }
      
        clientRoomSessionWatchId = webchatService.watchForRoomSessionMessages(roomId, sessionId, newMessagesReceived);
      
      
        evaluateIfReadyToPost();
      
      })
      .catch(function(errorReason) {
        if (errorReason == "LoginRequired") {
          
          $uibModal.open({
            templateUrl: 'modal-simple.html',
            controller: 'modalSimpleController',
            resolve: {
              config: function() {
                return {
                  mode: 'login-required',
                  message: 'You must log in to join a room.',
                  modalTitle: 'Login Required'
                }
              }
            }
          });
          
        }
        else {
          errorModalDefaultAlert("An error occurred in trying to enter the room.");
        }
      });
  }
  
  // User is ready to post if the session is created and recent messages have been fetched.
  var readyToPostConfirmed = false;
  
  var evaluateIfReadyToPost = function() {
    
    if (readyToPostConfirmed) {
      return;
    }
    
    if (recentRoomMessagesFetched && !angular.isUndefined(clientRoomSessionWatchId)) {
      $scope.messageInputTextPlaceholder = "Send a message";
      $scope.messageInputDisabled = false;
      
      focusSendMessageBox();
      readyToPostConfirmed = true;
    }
  }
  
  
  
  fetchRecentRoomMessages();
  createNewRoomSession();
  
  
  var unsentMessageConfirmed = function(clientMessageId, serverMessageId) {
    var unsentMessage = unsentMessageMap[clientMessageId];
    if (angular.isUndefined(unsentMessage)) {
      return;
    }
    
    confirmedSentMessageIdMap[clientMessageId] = true;
    unsentMessage["message-id"] = serverMessageId;
    if (unsentMessage.hasOwnProperty("send-failure")) {
      delete unsentMessage["send-failure"];
    }
    delete unsentMessage["unsent"];
    
    delete unsentMessageMap[clientMessageId];
  }
  
  var postUnsentMessage = function(messageText) {
    
    var unsentMessageObject = {
      "message-id": Guid.raw(),
      "client-message-id": Guid.raw(),
      "timestamp": Math.floor(Date.now() / 1000),
      "identity-id": userId,
      "author-name": userId,
      "message": messageText,
      "unsent": true
    };
    
    unsentMessageMap[unsentMessageObject["client-message-id"]] = unsentMessageObject;
    
    newMessagesReceived([unsentMessageObject], true);
    
    return unsentMessageObject;
  }
  
  $scope.messageSendFormSubmitted = function() {
    
    var messageText = $scope.messageInputText;
    
    var clientMessageId = Guid.raw();
    
    var unsentMessage = postUnsentMessage(messageText);
    var clientMessageId = unsentMessage["client-message-id"];
    $scope.messageInputText = "";
    focusSendMessageBox();
    
    var postRoomId = roomId;
    
    webchatService.postNewRoomMessage(postRoomId, messageText, clientMessageId)
      .then(function(serverMessageId) {
        unsentMessageConfirmed(clientMessageId, serverMessageId);
      })
      .catch(function() {
        if (unsentMessage.hasOwnProperty("unsent") && unsentMessage["unsent"]) {
          unsentMessage["send-failure"] = true;
        }
        else {
          console.log("Ignoring error in sending message already confirmed received.");
        }
      })
    
  }
  
  $scope.$on("$destroy", function() {
    if (!angular.isUndefined(clientRoomSessionWatchId)) {
      stopSessionWatchingSession(clientRoomSessionWatchId);
      clientRoomSessionWatchId = undefined;
    }
  });
  
});