'use strict';

app.controller('roomController', function($scope, $http, $stateParams, $cookieStore, $uibModal, webchatService, errorModalDefaultAlert, WebChatApiEndpoint) {
  
  $scope.roomChatEvents = [];
  $scope.messageInputDisabled = true;
  $scope.messageInputTextPlaceholder = "";
  $scope.roomLoadComplete = false;
  $scope.failedToCreateRoomSession = false;
  $scope.roomHistoryFetchesInProgress = 0;
  
  $scope.identityIdAuthorNameMap = {};
  var identityIdAvatarHashMap = {};
  
  var roomId = $stateParams.roomId;
  
  var unsentIdentityId = undefined;
  var unsentAuthorName = undefined;
  var roomHistoryIsCurrent = false;
  var fullRoomHistoryRetrieved = false;
  var initialRoomHistoryFetchComplete = false;
  var roomEventsWrapperElement = document.getElementById("webchat-event-group-wrapper");
  
  try {
    unsentIdentityId = $cookieStore.get("login")["user"]["user-id"];
    unsentAuthorName = $cookieStore.get("login")["user"]["email-address"];
  }
  catch (e) {
    // Do nothing.
  }
  
  
  var unsentMessageMap = {};
  var confirmedSentMessageIdMap = {};
  var addedMessageIdMap = {};
  
  var recentRoomMessagesFetched = false;
  var roomSessionId = undefined;
  var clientRoomSessionWatchId = undefined;
  
  var scrollLockEnabled = true;
  
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
  
  var mostRecentTimestampReceived = 0;
  
  var newMessagesReceived = function(messageArray, unsent) {
    
    if (unsent == null || unsent == undefined) {
      unsent = false;
    }
    
    var heightBefore = roomEventsWrapperElement.clientHeight;
    //console.log("Before: ", heightBefore);
    
    var mostRecentEventReceived = false;
    
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
            unsentMessageConfirmed(eachClientMessageId, eachMessage["message-id"], eachMessage);
            continue;
          }
          
          if (confirmedSentMessageIdMap.hasOwnProperty(eachClientMessageId)) {
            // We already know this message was confirmed.
            continue;
          }
        }
      }
      
      $scope.identityIdAuthorNameMap[eachMessage["identity-id"]] = eachMessage["author-name"];
      if (eachMessage.hasOwnProperty("author-avatar-hash")) {
        identityIdAvatarHashMap[eachMessage["identity-id"]] = eachMessage["author-avatar-hash"];
      }
      
      
      if (!addedMessageIdMap.hasOwnProperty(eachMessage["message-id"])) {
        addedMessageIdMap[eachMessage["message-id"]] = true;
        
        if (mostRecentTimestampReceived < eachMessage["timestamp"]) {
          mostRecentTimestampReceived = eachMessage["timestamp"];
          mostRecentEventReceived = true;
        }
        
        eachMessage["visible"] = eachMessage["type"] !== "SESSION_STARTED";
        eachMessage["timestamp-in-day"] = moment.unix(eachMessage["timestamp"]).format("LT");
        
        eachMessage.setAvatarUrl = function() {
          var avatarUrl = undefined;
        
          if (eachMessage["identity-id"] == "SYSTEM") {
            avatarUrl = "img/system-avatar-40x40.png";
          }
          else {
            avatarUrl = WebChatApiEndpoint + "user/" + eachMessage["identity-id"] + "/avatar?";
            avatarUrl += "s=40";
            avatarUrl += "&hash=" + encodeURIComponent(identityIdAvatarHashMap[eachMessage["identity-id"]]);
          }
          
          eachMessage["avatar-img-src"] = avatarUrl;
        }
        
        eachMessage.setAvatarUrl();
        
        $scope.roomChatEvents.push(eachMessage);
        
      }
    }
    
    $scope.roomChatEvents.sort(roomChatEventComparator);
    
    var previousVisibleMessageAuthorId = undefined;
    var previousVisibleMessageTimestamp = 0;
    
    for (var i=0; i < $scope.roomChatEvents.length; i++) {
      var eachMessage = $scope.roomChatEvents[i];
      
      var secondsSincePreviousTimestamp = eachMessage["timestamp"] - previousVisibleMessageTimestamp;
      
      eachMessage.previousMessageShouldBeGrouped = eachMessage["identity-id"] == previousVisibleMessageAuthorId && secondsSincePreviousTimestamp < 600;
      
      if (eachMessage["visible"]) {
        previousVisibleMessageAuthorId = eachMessage["identity-id"];
        previousVisibleMessageTimestamp = eachMessage["timestamp"];
      }
      
    }
    
    var heightAfter = roomEventsWrapperElement.clientHeight;
    
    
    //console.log("After: ", heightAfter);
    
    if (scrollLockEnabled && mostRecentEventReceived) {
      scrollToBottom();
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
  
  var loginRequiredModalShown = false;
  
  var showLoginRequiredModal = function() {
    if (loginRequiredModalShown) {
      return;
    }
    
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
    
    loginRequiredModalShown = true;
  }
  
  var firstRecentRoomMessageRequestOccurred = false;
  
  var fetchRecentRoomMessages = function(nextToken) {
    
    var isFirstRequest = (!firstRecentRoomMessageRequestOccurred);
    
    firstRecentRoomMessageRequestOccurred = true;
    
    $scope.roomHistoryFetchesInProgress++;
    
    webchatService.getRoomMessageHistory(roomId, nextToken)
      .then(function(response) {
        var messageArray = response.messages;
        
        newMessagesReceived(messageArray);
        recentRoomMessagesFetched = true;
        
        if (response.truncated) {
          
          if (!initialRoomHistoryFetchComplete) {
            if (document.documentElement.clientHeight < roomEventsWrapperElement.clientHeight) {
              console.log("Finished fetch of enough history to fill the screen.");
              initialRoomHistoryFetchComplete = true;
            }
            else {
              if (!$scope.failedToCreateRoomSession) {
                if (isFirstRequest || !angular.isUndefined(nextToken)) {
                  fetchRecentRoomMessages(response["next-token"]);
                }
              }
            }
          }
          
        }
        else {
          fullRoomHistoryRetrieved = true;
          console.log("Reached end of room's history.");
        }
        
        if (angular.isUndefined(nextToken)) {
          evaluateIfRecentRoomHistoryFetchComplete();
        }
        
        $scope.roomHistoryFetchesInProgress--;
      })
      .catch(function(errorReason) {
        $scope.roomHistoryFetchesInProgress--;
        console.log("An error occurred fetching recent room messages.");
        console.log(errorReason);
        
        if (errorReason == "LoginRequired") {
          showLoginRequiredModal();
        }
        else if (angular.isUndefined(nextToken)) {
          errorModalDefaultAlert("An error occurred fetching recent room messages.");
        }
        else {
          console.log("Trying again in a few seconds.");
          $scope.roomHistoryFetchesInProgress++;
          setTimeout(function() {
            $scope.roomHistoryFetchesInProgress--;
            fetchRecentRoomMessages(nextToken);
          }, 3000);
        }
      })
  }
  
  var createNewRoomSession = function() {
    webchatService.createNewRoomSession(roomId)
      .then(function(sessionId) {
      
        if (!angular.isUndefined(clientRoomSessionWatchId)) {
          stopSessionWatchingSession(clientRoomSessionWatchId);
          clientRoomSessionWatchId = undefined;
        }
        
        roomSessionId = sessionId;
      
        clientRoomSessionWatchId = webchatService.watchForRoomSessionMessages(roomId, sessionId, newMessagesReceived);
      
        evaluateIfRecentRoomHistoryFetchComplete();
        evaluateIfReadyToPost();
      
      })
      .catch(function(errorReason) {
        $scope.failedToCreateRoomSession = true;
        
        if (errorReason == "LoginRequired") {
          showLoginRequiredModal();
        }
        else {
          errorModalDefaultAlert(errorReason);
        }
      });
  }
  
  // User is ready to post if the session is created and recent messages have been fetched.
  var readyToPostConfirmed = false;
  var inviteFunctionalityUnderstood = false;
  
  var evaluateIfReadyToPost = function() {
    
    if (readyToPostConfirmed) {
      return;
    }
    
    
    
    if (roomHistoryIsCurrent && !angular.isUndefined(clientRoomSessionWatchId)) {
      
      $scope.messageInputTextPlaceholder = "Send a message";
      $scope.messageInputDisabled = false;
      
      focusSendMessageBox();
      readyToPostConfirmed = true;
      $scope.roomLoadComplete = true;
      scrollToBottom();
      
      if (!inviteFunctionalityUnderstood) {
        if (angular.isUndefined($cookieStore.get("invite-tutorial-shown"))) {
        
          $uibModal.open({
            templateUrl: 'modal-simple.html',
            controller: 'modalSimpleController',
            resolve: {
              config: function() {
                return {
                  mode: 'invite-tutorial'
                }
              }
            }
          });
        
          return;
        }
        else {
          inviteFunctionalityUnderstood = true;
        }
      }
      
      
    }
  }
  
  var evaluateIfRecentRoomHistoryFetchComplete = function() {
    
    if (roomHistoryIsCurrent) {
      return;
    }
    
    for (var i = 0; i < $scope.roomChatEvents.length; i++) {
      var eachEvent = $scope.roomChatEvents[i];
      
      if (eachEvent["identity-id"] == "SYSTEM" && eachEvent["type"] == "SESSION_STARTED") {
        if (eachEvent["message"] == roomSessionId) {
          roomHistoryIsCurrent = true;
          evaluateIfReadyToPost();
          break;
        }
      }
    }
    
    if (recentRoomMessagesFetched && !roomHistoryIsCurrent) {
      // Try fetching again until we get the message of our session's creation.
      
      if (!$scope.failedToCreateRoomSession) {
        console.log("Room history doesn't contain session creation. Fetching again.");
      
        setTimeout(fetchRecentRoomMessages, 1000);
      }
    }
  }
  
  fetchRecentRoomMessages();
  createNewRoomSession();
  
  var unsentMessageConfirmed = function(clientMessageId, serverMessageId, serverMessage) {
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
    
    if (!angular.isUndefined(serverMessage)) {
      if (serverMessage.hasOwnProperty("author-avatar-hash")) {
        unsentMessage["author-avatar-hash"] = serverMessage["author-avatar-hash"];
        unsentMessage.setAvatarUrl()
      }
    }
    
    delete unsentMessageMap[clientMessageId];
  }
  
  var postUnsentMessage = function(messageText) {
    
    var unsentMessageObject = {
      "message-id": Guid.raw(),
      "client-message-id": Guid.raw(),
      "timestamp": Math.floor(Date.now() / 1000),
      "identity-id": unsentIdentityId,
      "author-name": unsentAuthorName,
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
  
  // http://stackoverflow.com/a/10795797
  var getDocHeight = function() {
    var D = document;
    return Math.max(
      D.body.scrollHeight, D.documentElement.scrollHeight,
      D.body.offsetHeight, D.documentElement.offsetHeight,
      D.body.clientHeight, D.documentElement.clientHeight
    );
  }
  
  $(window).scroll(function() {
    if($(window).scrollTop() + $(window).height() == getDocHeight()) {
      scrollLockEnabled = true;
    }
    else {
      scrollLockEnabled = false;
    }
  });
  
  var scrollToBottom = function() {
    setTimeout(function() {
      window.scrollTo(0,document.body.scrollHeight);
    }, 0)
  }
  
  var scrollToTop = function() {
    setTimeout(function() {
      window.scrollTo(0,0);
    }, 0);
  }
  
  // Start at top.
  scrollToTop();
  
  $scope.$on("$destroy", function() {
    scrollToTop();
  })
  
})
.directive("roomLoadingActivityIndicator", function() {
  
  var link = function(scope, element, attrs) {
    var spinner = new Spinner({}).spin(element.children()[0]);
  }
  
  return {
    link: link,
    restrict: 'A',
    template: '<div></div>'
  };
});